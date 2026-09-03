"""Human escalation and safety monitoring (Checkpoint 6.1)."""

from __future__ import annotations

from typing import Any

from config import settings

ESCALATION_REASONS = {
    "low_confidence": "Overall confidence below threshold",
    "incomplete_evidence": "Evidence incomplete after max retrieval cycles",
    "conflicting_evidence": "Contradictory evidence could not be resolved",
    "unverified_claims": "Critical claims lack multi-source verification",
    "outdated_information": "Retrieved information appears outdated",
    "policy_violation": "Possible policy violation detected",
    "retrieval_failure": "Repeated retrieval failures",
    "high_impact_low_evidence": "High-impact recommendations depend on limited evidence",
}


def compute_overall_confidence(state: dict[str, Any]) -> float:
    """Compute aggregate confidence from findings and analysis."""
    findings = state.get("findings", [])
    if not findings:
        return 0.0

    finding_confidence = sum(f.get("confidence", 0) for f in findings) / len(findings)
    tot_confidence = state.get("tot_confidence", 0.5)
    verification_rate = state.get("verification_results", {}).get("verification_rate", 0.5)

    return round(
        finding_confidence * 0.4 + tot_confidence * 0.3 + verification_rate * 0.3,
        3,
    )


def detect_conflicts(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect contradictory claims for the same company/category."""
    by_key: dict[str, list[dict[str, Any]]] = {}

    for finding in findings:
        key = f"{finding.get('company')}:{finding.get('category', '').lower()}"
        by_key.setdefault(key, []).append(finding)

    conflicts: list[dict[str, Any]] = []
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        claims = {f.get("claim", "") for f in group}
        if len(claims) > 1:
            conflicts.append(
                {
                    "key": key,
                    "claims": list(claims),
                    "sources": [f.get("source_url") for f in group],
                }
            )

    return conflicts


def should_escalate(state: dict[str, Any]) -> dict[str, Any]:
    """
    Determine if human review is required before report generation.
    Checkpoint 6.1: escalate when confidence < 70% or evidence issues persist.
    """
    reasons: list[str] = []
    overall_confidence = compute_overall_confidence(state)

    if overall_confidence < settings.escalation_confidence_threshold:
        reasons.append(ESCALATION_REASONS["low_confidence"])

    missing = state.get("missing_information", [])
    iteration = state.get("iteration_count", 0)
    if missing and iteration >= settings.max_research_iterations:
        reasons.append(ESCALATION_REASONS["incomplete_evidence"])

    conflicts = detect_conflicts(state.get("findings", []))
    if conflicts:
        reasons.append(ESCALATION_REASONS["conflicting_evidence"])

    verification = state.get("verification_results", {})
    if verification.get("unverified_claims") and verification.get("verification_rate", 1) < 0.5:
        reasons.append(ESCALATION_REASONS["unverified_claims"])

    recommendations = state.get("recommendations", [])
    if recommendations and overall_confidence < 0.6:
        reasons.append(ESCALATION_REASONS["high_impact_low_evidence"])

    errors = state.get("errors", [])
    retrieval_errors = [e for e in errors if "search failed" in e.lower() or "retrieval" in e.lower()]
    if len(retrieval_errors) >= 3:
        reasons.append(ESCALATION_REASONS["retrieval_failure"])

    return {
        "requires_human_review": len(reasons) > 0,
        "escalation_reasons": reasons,
        "overall_confidence": overall_confidence,
        "conflicts": conflicts,
        "threshold": settings.escalation_confidence_threshold,
    }


def format_escalation_summary(escalation: dict[str, Any]) -> str:
    """Format escalation details for human reviewers."""
    if not escalation.get("requires_human_review"):
        return ""

    lines = [
        "## Human Review Required",
        "",
        f"**Overall Confidence:** {escalation['overall_confidence']:.0%} (threshold: {escalation['threshold']:.0%})",
        "",
        "**Escalation Reasons:**",
    ]
    for reason in escalation["escalation_reasons"]:
        lines.append(f"- {reason}")

    conflicts = escalation.get("conflicts", [])
    if conflicts:
        lines.append("")
        lines.append("**Conflicting Evidence:**")
        for conflict in conflicts[:5]:
            lines.append(f"- {conflict['key']}: {len(conflict['claims'])} conflicting claims")

    lines.append("")
    lines.append(
        "An analyst should approve, request additional research, correct interpretations, "
        "or reject unsupported conclusions before the report is finalized."
    )

    return "\n".join(lines)
