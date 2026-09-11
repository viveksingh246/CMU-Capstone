"""Formatting helpers for strategic recommendation presentation."""

from __future__ import annotations

from typing import Any


def recommendation_basis(rec: dict[str, Any]) -> str:
    """Return the evidence / rationale text backing a recommendation."""
    for key in ("evidence", "rationale", "basis", "supporting_evidence", "reason"):
        value = rec.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for nested in ("summary", "note", "detail", "evidence"):
                nested_value = value.get(nested)
                if isinstance(nested_value, str) and nested_value.strip():
                    return nested_value.strip()
    return ""


def recommendation_meta_line(rec: dict[str, Any]) -> str:
    priority = rec.get("priority", "Medium")
    impact = rec.get("impact", "Strategic impact")
    horizon = rec.get("time_horizon", "Medium-term")
    return f"{priority} priority · Impact: {impact} · Horizon: {horizon}"


def build_recommendations_intro(result: dict[str, Any]) -> str:
    """Context line for the recommendations section header."""
    findings_count = len(result.get("findings", []))
    escalation = result.get("escalation", {})
    confidence = escalation.get("overall_confidence", result.get("tot_confidence", 0))
    hypothesis = (result.get("selected_hypothesis") or "").strip()

    intro = (
        f"Evidence-backed actions from {findings_count} validated findings "
        f"at {confidence:.0%} overall confidence"
    )
    if hypothesis:
        short_hypothesis = hypothesis if len(hypothesis) <= 140 else f"{hypothesis[:137]}..."
        intro += f". Grounded in the leading hypothesis: {short_hypothesis}"
    intro += "."
    return intro
