"""Tests for recommendation presentation helpers."""

from ui.recommendation_view import (
    build_recommendations_intro,
    recommendation_basis,
    recommendation_meta_line,
)


def test_recommendation_basis_prefers_evidence_field():
    rec = {
        "recommendation": "Expand partnerships",
        "evidence": "Validated findings show weak institutional coverage.",
        "rationale": "ignored",
    }
    assert recommendation_basis(rec) == "Validated findings show weak institutional coverage."


def test_recommendation_basis_reads_nested_rationale_dict():
    rec = {"rationale": {"summary": "Scorecard gap in AI maturity vs peers."}}
    assert recommendation_basis(rec) == "Scorecard gap in AI maturity vs peers."


def test_build_recommendations_intro_includes_confidence_and_hypothesis():
    result = {
        "findings": [{}, {}],
        "escalation": {"overall_confidence": 0.72},
        "selected_hypothesis": "Coursera leads on breadth but Udemy is closing the AI gap.",
    }
    intro = build_recommendations_intro(result)
    assert "2 validated findings" in intro
    assert "72%" in intro
    assert "Coursera leads" in intro


def test_recommendation_meta_line_formats_priority_impact_horizon():
    line = recommendation_meta_line(
        {"priority": "High", "impact": "Revenue", "time_horizon": "6 months"}
    )
    assert "High priority" in line
    assert "Revenue" in line
    assert "6 months" in line
