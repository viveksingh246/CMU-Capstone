"""Tests for the Validation Agent."""

from agents.validator import validate_evidence


def _finding(**overrides):
    base = {
        "company": "Snowflake",
        "category": "Products",
        "claim": "Cloud data warehouse platform",
        "evidence": "Official documentation describes a cloud-native data warehouse with separation of storage and compute.",
        "source_url": "https://snowflake.com/products",
        "source_type": "official_website",
        "confidence": 0.9,
        "is_company_claim": False,
    }
    base.update(overrides)
    return base


def test_validate_evidence_keeps_high_confidence_findings():
    state = {"findings": [_finding()], "errors": []}
    result = validate_evidence(state)

    assert len(result["findings"]) == 1
    assert result["findings"][0]["claim_type"] == "verified_fact"
    assert "verification_results" in result


def test_validate_evidence_filters_low_confidence():
    state = {"findings": [_finding(confidence=0.3)], "errors": []}
    result = validate_evidence(state)

    assert len(result["findings"]) == 0
    assert any("Filtered" in e for e in result["errors"])


def test_validate_evidence_deduplicates_claims():
    state = {"findings": [_finding(), _finding()], "errors": []}
    result = validate_evidence(state)

    assert len(result["findings"]) == 1


def test_validate_evidence_labels_company_claims():
    state = {"findings": [_finding(is_company_claim=True)], "errors": []}
    result = validate_evidence(state)

    assert result["findings"][0]["claim_type"] == "company_statement"


def test_validate_evidence_records_react_step():
    state = {"findings": [_finding()], "errors": [], "short_term_memory": {}}
    result = validate_evidence(state)

    assert result["short_term_memory"]["reasoning_steps"][-1]["phase"] == "reflect"
