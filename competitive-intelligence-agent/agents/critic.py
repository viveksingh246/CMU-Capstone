"""Critic agent for Tree-of-Thought branch evaluation (Checkpoint 4.1)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

# Checkpoint 4.1 scoring weights
SCORING_WEIGHTS = {
    "source_credibility": 0.25,
    "evidence_completeness": 0.20,
    "evidence_freshness": 0.20,
    "cross_source_consistency": 0.15,
    "strategic_relevance": 0.10,
    "reasoning_confidence": 0.10,
}

OFFICIAL_SOURCE_TYPES = {
    "official_website",
    "official_documentation",
    "regulatory_filing",
    "press_release",
    "official_blog",
}


def evaluate_branch(branch: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Score a reasoning branch using the checkpoint 4.1 rubric.
    Returns per-criterion scores and overall weighted score (0-100).
    """
    evidence = branch.get("supporting_evidence", findings)

    scores = {
        "source_credibility": _score_source_credibility(evidence),
        "evidence_completeness": _score_completeness(evidence, branch),
        "evidence_freshness": _score_freshness(evidence),
        "cross_source_consistency": _score_consistency(evidence),
        "strategic_relevance": _score_strategic_relevance(branch),
        "reasoning_confidence": branch.get("confidence_score", 0.5) * 100,
    }

    overall = sum(scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)

    return {
        "criterion_scores": scores,
        "overall_score": round(overall, 2),
        "pruned": overall < 65,
        "evaluation_notes": _generate_notes(scores),
    }


def _score_source_credibility(evidence: list[dict[str, Any]]) -> float:
    if not evidence:
        return 20.0

    credibility_values = []
    for item in evidence:
        source_type = str(item.get("source_type", "other"))
        if source_type in OFFICIAL_SOURCE_TYPES:
            credibility_values.append(100)
        elif source_type in ("news", "research_paper"):
            credibility_values.append(80)
        elif source_type in ("github", "job_posting"):
            credibility_values.append(60)
        else:
            credibility_values.append(40)

    return sum(credibility_values) / len(credibility_values)


def _score_completeness(evidence: list[dict[str, Any]], branch: dict[str, Any]) -> float:
    if not evidence:
        return 10.0

    base = min(len(evidence) * 15, 80)
    unresolved = len(branch.get("unresolved_questions", []))
    penalty = min(unresolved * 10, 40)
    return max(base - penalty, 10)


def _score_freshness(evidence: list[dict[str, Any]]) -> float:
    if not evidence:
        return 30.0

    cutoff = datetime.utcnow() - timedelta(days=365)
    fresh_count = 0

    for item in evidence:
        pub_date = item.get("published_date")
        if not pub_date:
            fresh_count += 1
            continue
        try:
            parsed = datetime.fromisoformat(str(pub_date).replace("Z", "+00:00").split("T")[0])
            if parsed.replace(tzinfo=None) >= cutoff:
                fresh_count += 1
        except ValueError:
            fresh_count += 1

    return (fresh_count / len(evidence)) * 100


def _score_consistency(evidence: list[dict[str, Any]]) -> float:
    if len(evidence) < 2:
        return 50.0

    companies = {item.get("company") for item in evidence if item.get("company")}
    categories = {item.get("category") for item in evidence if item.get("category")}

    diversity_score = min(len(companies) * 20 + len(categories) * 10, 80)

    confidences = [item.get("confidence", 0.5) for item in evidence]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

    return min(diversity_score + avg_confidence * 20, 100)


def _score_strategic_relevance(branch: dict[str, Any]) -> float:
    branch_type = branch.get("branch_type", "")
    valid_types = {
        "innovation_leadership",
        "pricing_competitiveness",
        "partnership_strength",
        "engineering_momentum",
    }
    if branch_type in valid_types:
        return 85.0
    if branch.get("hypothesis"):
        return 70.0
    return 40.0


def _generate_notes(scores: dict[str, float]) -> list[str]:
    notes: list[str] = []
    for criterion, score in scores.items():
        if score < 50:
            notes.append(f"Low {criterion.replace('_', ' ')}: {score:.0f}/100")
    return notes
