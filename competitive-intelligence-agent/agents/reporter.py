"""Report generation agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import (
    LLMBudgetExhausted,
    can_invoke_llm,
    get_llm,
    invoke_llm,
    is_cloud_efficiency_mode,
    load_prompt,
)
from memory.schemas import CompetitiveReport
from workflows.state import ResearchState

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def _generate_template_report(state: ResearchState, sources: list[dict[str, str]]) -> str:
    """Deterministic markdown report — no LLM call (cloud efficiency mode)."""
    industry = state.get("industry", "")
    companies = state.get("companies", [])
    comparison = state.get("comparison", {})
    scorecard = state.get("scorecard", [])
    recommendations = state.get("recommendations", [])
    findings = state.get("findings", [])
    hypothesis = state.get("selected_hypothesis", "")

    lines = [
        "# Competitive Intelligence Report",
        "",
        "## Executive Summary",
        f"Analysis of **{', '.join(companies)}** in **{industry}**.",
        hypothesis or "Strategic assessment based on validated public evidence.",
        "",
        "## Market Overview",
        f"Compared {len(companies)} companies across {len(state.get('categories', []))} categories.",
        "",
        "## Company Profiles",
    ]
    for company in companies:
        company_findings = [f for f in findings if f.get("company") == company]
        lines.append(f"### {company}")
        lines.append(f"- {len(company_findings)} validated findings")
        lines.append("")

    lines.extend(["## Product Comparison Matrix", str(comparison.get("feature_matrix", {})), ""])
    lines.extend(["## Pricing Comparison", str(comparison.get("pricing_comparison", {})), ""])
    lines.extend(["## Recent Strategic Moves", str(comparison.get("strategic_moves", [])), ""])
    lines.extend(["## AI Capability Analysis", str(comparison.get("ai_analysis", {})), ""])
    lines.extend(["## Competitive Scorecard", json.dumps(scorecard, indent=2), ""])
    lines.extend(["## Key Trends", str(comparison.get("key_trends", [])), ""])
    lines.extend(["## Strategic Recommendations"])
    for rec in recommendations[:10]:
        if isinstance(rec, dict):
            lines.append(f"- **{rec.get('priority', 'Medium')}**: {rec.get('recommendation', '')}")
        else:
            lines.append(f"- {rec}")
    lines.extend(["", "## Sources"])
    for source in sources:
        lines.append(f"- [{source.get('title', 'Source')}]({source.get('url', '')})")
    return "\n".join(lines)


def generate_report(state: ResearchState) -> dict[str, Any]:
    """Generate the final executive competitive intelligence report."""
    report_input = {
        "industry": state.get("industry"),
        "companies": state.get("companies"),
        "categories": state.get("categories"),
        "findings": state.get("findings", [])[:30],
        "comparison": state.get("comparison", {}),
        "swot": state.get("swot_analysis", {}),
        "scorecard": state.get("scorecard", []),
        "recommendations": state.get("recommendations", []),
        "historical_changes": state.get("historical_changes", []),
        "alerts": state.get("alerts", []),
        "category_completeness": state.get("category_completeness", {}),
        "selected_hypothesis": state.get("selected_hypothesis", ""),
        "tot_confidence": state.get("tot_confidence", 0),
        "evaluation_metrics": state.get("evaluation_metrics", {}),
        "escalation": state.get("escalation", {}),
        "sources": _build_sources_list(state.get("findings", [])),
    }

    sources = report_input["sources"]
    use_template = is_cloud_efficiency_mode() or not can_invoke_llm()

    if use_template:
        final_report = _generate_template_report(state, sources)
        status_suffix = " (template, no LLM)"
    else:
        llm = get_llm()
        system_prompt = load_prompt("report")
        user_content = f"""
Generate an executive competitive intelligence report in Markdown format.

Input data:
{json.dumps(report_input, indent=2, default=str)}

The report must include:
1. Executive Summary
2. Market Overview
3. Company Profiles
4. Product Comparison Matrix
5. Pricing Comparison
6. Recent Strategic Moves
7. Hiring Signals
8. AI Capability Analysis
9. SWOT Analysis (per company)
10. Competitive Scorecard
11. Key Trends
12. Strategic Recommendations
13. Sources

Guardrails:
- Every important claim must reference a source
- Mark unknown information as "not publicly available"
- Label marketing statements as company claims
- Distinguish facts from analysis
- Note any incomplete categories
"""
        try:
            response = invoke_llm(
                llm,
                [SystemMessage(content=system_prompt), HumanMessage(content=user_content)],
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(str(part) for part in content)
            final_report = str(content)
            status_suffix = ""
        except LLMBudgetExhausted:
            final_report = _generate_template_report(state, sources)
            status_suffix = " (template fallback — LLM budget exhausted)"

    report_data = CompetitiveReport(
        executive_summary=_extract_section(final_report, "Executive Summary"),
        market_overview=_extract_section(final_report, "Market Overview"),
        company_profiles={},
        feature_matrix=state.get("comparison", {}).get("feature_matrix", {}),
        pricing_comparison=state.get("comparison", {}).get("pricing_comparison", {}),
        strategic_moves=state.get("comparison", {}).get("strategic_moves", []),
        hiring_signals=state.get("comparison", {}).get("hiring_signals", {}),
        ai_analysis=state.get("comparison", {}).get("ai_analysis", {}),
        swot=[],
        scorecard=[],
        key_trends=state.get("comparison", {}).get("key_trends", []),
        recommendations=[],
        sources=sources,
        historical_changes=[],
        alerts=[],
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"report_{timestamp}.md"
    report_path.write_text(final_report, encoding="utf-8")

    json_path = REPORTS_DIR / f"report_{timestamp}.json"
    json_path.write_text(
        json.dumps(report_data.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    return {
        "final_report": final_report,
        "report_data": report_data.model_dump(),
        "status_message": f"Report saved to {report_path.name}{status_suffix}",
    }


def _build_sources_list(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for f in findings:
        url = f.get("source_url", "")
        if url and url not in seen:
            seen.add(url)
            sources.append(
                {
                    "url": url,
                    "title": f.get("source_title", ""),
                    "date": f.get("published_date") or "Unknown",
                    "type": str(f.get("source_type", "other")),
                }
            )
    return sources


def _extract_section(report: str, heading: str) -> str:
    lines = report.split("\n")
    section_lines: list[str] = []
    in_section = False
    for line in lines:
        if heading.lower() in line.lower() and line.startswith("#"):
            in_section = True
            continue
        if in_section and line.startswith("#") and heading.lower() not in line.lower():
            break
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines).strip()
