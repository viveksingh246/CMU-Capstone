"""Competitive analysis agent."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm, load_prompt
from memory.schemas import Alert, CompanyScore, CompanySWOT, Recommendation
from workflows.state import ResearchState


def analyze_competitors(state: ResearchState) -> dict[str, Any]:
    """Compare companies and generate SWOT, scores, and recommendations."""
    findings = state.get("findings", [])
    companies = state.get("companies", [])
    categories = state.get("categories", [])
    industry = state.get("industry", "")

    llm = get_llm()
    system_prompt = load_prompt("analysis")

    findings_summary = json.dumps(findings[:50], indent=2)

    user_content = f"""
Industry: {industry}
Companies: {', '.join(companies)}
Categories: {', '.join(categories)}

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

Base all conclusions on the provided findings. Mark unsupported areas as "not publicly available".
Scores are analytical assessments (1=weak, 5=market-leading), not absolute facts.
"""

    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
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

        swot = [CompanySWOT.model_validate(s).model_dump() for s in analysis.get("swot", [])]
        scorecard = [
            CompanyScore.model_validate(s).model_dump() for s in analysis.get("scorecard", [])
        ]
        for score in scorecard:
            score["overall_score"] = CompanyScore.model_validate(score).overall_score

        recommendations = [
            Recommendation.model_validate(r).model_dump()
            for r in analysis.get("recommendations", [])
        ]

        return {
            "comparison": analysis.get("comparison", {}),
            "swot_analysis": {"companies": swot},
            "scorecard": scorecard,
            "recommendations": recommendations,
            "status_message": "Competitive analysis complete",
        }
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "comparison": {},
            "swot_analysis": {},
            "scorecard": [],
            "recommendations": [],
            "errors": state.get("errors", []) + [f"Analysis failed: {exc}"],
            "status_message": "Analysis completed with errors",
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
