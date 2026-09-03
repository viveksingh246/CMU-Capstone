"""Extended tests for safety guardrails (Checkpoint 6.1)."""

import pytest

from safety.guardrails import (
    InputValidationError,
    check_output_constraints,
    filter_approved_sources,
    validate_research_request,
    verify_multi_source,
)


def test_validate_rejects_too_many_companies():
    with pytest.raises(InputValidationError) as exc:
        validate_research_request("AI", ["A", "B", "C", "D", "E", "F"], ["Products"])
    assert any("5 companies" in v for v in exc.value.violations)


def test_validate_rejects_empty_categories():
    with pytest.raises(InputValidationError):
        validate_research_request("AI", ["A", "B"], [])


def test_validate_rejects_empty_industry():
    with pytest.raises(InputValidationError):
        validate_research_request("", ["A", "B"], ["Products"])


def test_filter_approved_sources_keeps_public_types():
    findings = [
        {"source_type": "official_website", "claim": "A"},
        {"source_type": "news", "claim": "B"},
        {"source_type": "other", "claim": "C"},
    ]
    approved, warnings = filter_approved_sources(findings)
    assert len(approved) == 3
    assert warnings == []


def test_check_output_constraints_analytical_assessment():
    result = check_output_constraints({
        "claim": "Likely leader",
        "confidence": 0.6,
        "source_url": "https://example.com",
    })
    assert result["claim_type"] == "analytical_assessment"


def test_verify_multi_source_all_verified():
    findings = [
        {"company": "A", "category": "X", "claim": "Same claim text here", "source_url": "https://a.com"},
        {"company": "A", "category": "X", "claim": "Same claim text here", "source_url": "https://b.com"},
    ]
    result = verify_multi_source(findings, min_sources=2)
    assert result["verification_rate"] == 1.0
    assert len(result["unverified_claims"]) == 0
