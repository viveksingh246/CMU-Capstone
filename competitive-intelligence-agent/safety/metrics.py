"""Evaluation metrics for safety and quality monitoring (Checkpoint 6.1)."""

from __future__ import annotations

from typing import Any


def compute_evaluation_metrics(state: dict[str, Any]) -> dict[str, Any]:
    """Compute quality and safety metrics for a research run."""
    findings = state.get("findings", [])
    categories = state.get("categories", [])
    companies = state.get("companies", [])

    # Correctness: verified findings ratio
    verified = [f for f in findings if f.get("claim_type") == "verified_fact" or f.get("confidence", 0) >= 0.7]
    correctness = len(verified) / len(findings) if findings else 0

    # Groundedness: findings with source URLs
    cited = [f for f in findings if f.get("source_url")]
    groundedness = len(cited) / len(findings) if findings else 0

    # Source credibility: official/trusted sources
    trusted_types = {
        "official_website", "official_documentation", "regulatory_filing",
        "press_release", "official_blog", "news",
    }
    trusted = [f for f in findings if str(f.get("source_type", "")) in trusted_types]
    source_credibility = len(trusted) / len(findings) if findings else 0

    # Freshness: findings with publication dates
    dated = [f for f in findings if f.get("published_date")]
    freshness = len(dated) / len(findings) if findings else 0

    # Research coverage
    completeness = state.get("category_completeness", {})
    complete_count = sum(1 for v in completeness.values() if v == "complete")
    coverage = complete_count / len(categories) if categories else 0

    # Safety compliance
    unlabeled = [f for f in findings if not f.get("claim_type")]
    safety_compliance = 1 - (len(unlabeled) / len(findings)) if findings else 1

    escalation = state.get("escalation", {})
    human_escalation = 1 if escalation.get("requires_human_review") else 0

    return {
        "correctness": {
            "value": round(correctness, 3),
            "target": 0.95,
            "passed": correctness >= 0.95,
        },
        "groundedness": {
            "value": round(groundedness, 3),
            "target": 1.0,
            "passed": groundedness >= 0.90,
        },
        "source_credibility": {
            "value": round(source_credibility, 3),
            "target": 0.70,
            "passed": source_credibility >= 0.70,
        },
        "freshness": {
            "value": round(freshness, 3),
            "target": 0.50,
            "passed": freshness >= 0.50,
        },
        "research_coverage": {
            "value": round(coverage, 3),
            "target": 0.90,
            "passed": coverage >= 0.90,
        },
        "safety_compliance": {
            "value": round(safety_compliance, 3),
            "target": 1.0,
            "passed": safety_compliance >= 0.95,
        },
        "human_escalation": {
            "value": human_escalation,
            "description": "1 = escalated for human review",
        },
        "companies_analyzed": len(companies),
        "findings_count": len(findings),
    }
