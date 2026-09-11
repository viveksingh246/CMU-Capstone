"""Competitive analysis agent."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm, invoke_llm, is_cloud_efficiency_mode, load_prompt, LLMBudgetExhausted
from memory.schemas import Alert, CompanyScore, CompanySWOT, Recommendation
from memory.short_term import record_react_step
from reasoning.tot_engine import beam_search_analysis
from workflows.state import ResearchState


def _sanitize_swot(swot_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop non-integer evidence_ids — small LLMs often return labels instead of IDs."""
    sanitized: list[dict[str, Any]] = []
    for entry in swot_data:
        cleaned = dict(entry)
        for section in ("strengths", "weaknesses", "opportunities", "threats"):
            points = []
            for point in cleaned.get(section, []):
                point_dict = dict(point)
                raw_ids = point_dict.get("evidence_ids", [])
                point_dict["evidence_ids"] = [
                    item for item in raw_ids if isinstance(item, int) and not isinstance(item, bool)
                ]
                points.append(point_dict)
            cleaned[section] = points
        sanitized.append(cleaned)
    return sanitized


def analyze_competitors(state: ResearchState) -> dict[str, Any]:
    """Compare companies using Tree-of-Thought reasoning, SWOT, scores, and recommendations."""
    findings = state.get("findings", [])
    companies = state.get("companies", [])
    categories = state.get("categories", [])
    industry = state.get("industry", "")

    # Tree-of-Thought beam search analysis (Checkpoint 4.1)
    tot_result = beam_search_analysis(companies, findings, industry)

    try:
        llm = get_llm()
    except ValueError:
        return _fallback_analysis(state, companies, categories, industry, tot_result)

    system_prompt = load_prompt("analysis")

    findings_summary = json.dumps(findings[:50], indent=2)
    tot_summary = json.dumps(tot_result.get("best_branch", {}), indent=2)

    user_content = f"""
Industry: {industry}
Companies: {', '.join(companies)}
Categories: {', '.join(categories)}

Tree-of-Thought selected hypothesis:
{tot_result.get('selected_hypothesis', '')}
ToT confidence: {tot_result.get('tot_confidence', 0):.0%}

Best reasoning branch:
{tot_summary}

Validated findings:
{findings_summary}

Generate a competitive analysis as JSON with:
{{
  "comparison": {{
    "feature_matrix": {{}},
    "pricing_comparison": {{}},
    "strategic_moves": [],
    "hiring_signals": {{}},
    "ai_analysis": {{}},
    "key_trends": []
  }},
  "swot": [
    {{
      "company": "...",
      "strengths": [{{"point": "...", "evidence_ids": []}}],
      "weaknesses": [...],
      "opportunities": [...],
      "threats": [...]
    }}
  ],
  "scorecard": [
    {{
      "company": "...",
      "product_breadth": 3.0,
      "feature_differentiation": 3.0,
      "pricing_attractiveness": 3.0,
      "ai_maturity": 3.0,
      "partnerships": 3.0,
      "innovation_momentum": 3.0,
      "hiring_momentum": 3.0,
      "rationale": {{}}
    }}
  ],
  "recommendations": [
    {{
      "recommendation": "...",
      "evidence": "...",
      "impact": "...",
      "priority": "High|Medium|Low",
      "time_horizon": "..."
    }}
  ]
}}

Base all conclusions on the provided findings and ToT analysis.
Mark unsupported areas as "not publicly available".
Scores are analytical assessments (1=weak, 5=market-leading), not absolute facts.
"""

    try:
        response = invoke_llm(
            llm,
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)],
        )
        content = response.content
        if isinstance(content, list):
            content = "".join(str(part) for part in content)

        text = str(content).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        analysis = json.loads(text)

        swot = [
            CompanySWOT.model_validate(s).model_dump()
            for s in _sanitize_swot(analysis.get("swot", []))
        ]
        scorecard = [
            CompanyScore.model_validate(s).model_dump() for s in analysis.get("scorecard", [])
        ]
        for score in scorecard:
            score["overall_score"] = CompanyScore.model_validate(score).overall_score

        recommendations = [
            Recommendation.model_validate(r).model_dump()
            for r in analysis.get("recommendations", [])
        ]

        react = record_react_step(
            state,
            "decide",
            "Selected best ToT branch for competitive analysis",
            tot_result.get("selected_hypothesis", ""),
            {"tot_confidence": tot_result.get("tot_confidence", 0)},
        )

        return {
            **react,
            "comparison": analysis.get("comparison", {}),
            "swot_analysis": {"companies": swot},
            "scorecard": scorecard,
            "recommendations": recommendations,
            "tot_analysis": tot_result,
            "tot_confidence": tot_result.get("tot_confidence", 0),
            "selected_hypothesis": tot_result.get("selected_hypothesis", ""),
            "status_message": "Competitive analysis complete (ToT beam search)",
        }
    except (json.JSONDecodeError, ValueError) as exc:
        result = _fallback_analysis(state, companies, categories, industry, tot_result)
        result["errors"] = state.get("errors", []) + [f"Analysis failed: {exc}"]
        result["status_message"] = "Analysis completed with errors (LLM parse fallback)"
        return result
    except LLMBudgetExhausted:
        result = _fallback_analysis(state, companies, categories, industry, tot_result)
        result["status_message"] = "Competitive analysis complete (budget-safe fallback)"
        return result


def _fallback_analysis(
    state: ResearchState,
    companies: list[str],
    categories: list[str],
    industry: str,
    tot_result: dict[str, Any],
) -> dict[str, Any]:
    """Deterministic analysis when LLM is unavailable, grounded in ToT results."""
    scorecard = [
        CompanyScore(
            company=company,
            product_breadth=3.0,
            feature_differentiation=3.0,
            pricing_attractiveness=3.0,
            ai_maturity=3.0,
            partnerships=3.0,
            innovation_momentum=3.0,
            hiring_momentum=3.0,
            rationale={"note": "Analytical assessment based on available evidence"},
        ).model_dump()
        for company in companies
    ]
    for score in scorecard:
        score["overall_score"] = CompanyScore.model_validate(score).overall_score

    react = record_react_step(
        state,
        "decide",
        "ToT fallback analysis (LLM unavailable)",
        tot_result.get("selected_hypothesis", ""),
    )

    return {
        **react,
        "comparison": {
            "feature_matrix": {c: "See validated findings" for c in companies},
            "pricing_comparison": {c: "not publicly available" for c in companies},
            "strategic_moves": [],
            "hiring_signals": {},
            "ai_analysis": {"hypothesis": tot_result.get("selected_hypothesis", "")},
            "key_trends": [f"Analysis based on {len(state.get('findings', []))} validated findings"],
        },
        "swot_analysis": {"companies": []},
        "scorecard": scorecard,
        "recommendations": [],
        "tot_analysis": tot_result,
        "tot_confidence": tot_result.get("tot_confidence", 0),
        "selected_hypothesis": tot_result.get("selected_hypothesis", ""),
        "status_message": "Competitive analysis complete (ToT fallback, no LLM)",
    }


def detect_historical_changes(state: ResearchState) -> dict[str, Any]:
    """Compare current findings with previous research runs."""
    if not state.get("include_historical_comparison"):
        return {"historical_changes": [], "alerts": []}

    previous = state.get("previous_findings", [])
    current = state.get("findings", [])
    changes: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []

    prev_by_key = {
        f"{p.get('company')}:{p.get('category')}:{p.get('claim', '')[:80]}": p
        for p in previous
    }

    for finding in current:
        key = f"{finding.get('company')}:{finding.get('category')}:{finding.get('claim', '')[:80]}"
        if key not in prev_by_key:
            change = {
                "company": finding.get("company"),
                "change_type": "new_finding",
                "description": finding.get("claim", ""),
                "current_value": finding.get("claim"),
            }
            changes.append(change)

            if state.get("generate_alerts") and finding.get("category") in (
                "pricing",
                "products",
                "AI capabilities",
                "partnerships",
            ):
                alert = Alert(
                    company=finding.get("company", ""),
                    alert_type=finding.get("category", "update"),
                    description=finding.get("claim", ""),
                    source_url=finding.get("source_url"),
                    priority="high" if "pricing" in finding.get("category", "").lower() else "medium",
                )
                alerts.append(alert.model_dump())

    # Detect pricing changes
    prev_pricing = {
        p.get("company"): p.get("claim")
        for p in previous
        if "pricing" in p.get("category", "").lower()
    }
    curr_pricing = {
        f.get("company"): f.get("claim")
        for f in current
        if "pricing" in f.get("category", "").lower()
    }

    for company, new_claim in curr_pricing.items():
        old_claim = prev_pricing.get(company)
        if old_claim and old_claim != new_claim:
            changes.append(
                {
                    "company": company,
                    "change_type": "pricing_change",
                    "description": f"Pricing information changed for {company}",
                    "previous_value": old_claim,
                    "current_value": new_claim,
                }
            )

    return {"historical_changes": changes, "alerts": alerts}
