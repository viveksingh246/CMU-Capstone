"""Tests for safety guardrails and escalation (Checkpoint 6.1)."""

import pytest

from safety.escalation import should_escalate
from safety.guardrails import InputValidationError, check_output_constraints, validate_research_request, verify_multi_source
from safety.metrics import compute_evaluation_metrics


def test_validate_research_request_success():
    result = validate_research_request(
        "Cloud Data Platforms",
        ["Snowflake", "Databricks"],
        ["Products", "Pricing"],
    )
    assert result["validated"] is True
    assert len(result["companies"]) == 2


def test_validate_research_request_rejects_too_few_companies():
    with pytest.raises(InputValidationError):
        validate_research_request("AI", ["Snowflake"], ["Products"])


def test_validate_research_request_rejects_confidential():
    with pytest.raises(InputValidationError):
        validate_research_request(
            "confidential internal financial data",
            ["Snowflake", "Databricks"],
            ["Products"],
        )


def test_verify_multi_source():
    findings = [
        {"company": "A", "category": "Pricing", "claim": "Pay per use", "source_url": "https://a.com/1"},
        {"company": "A", "category": "Pricing", "claim": "Pay per use", "source_url": "https://b.com/2"},
        {"company": "B", "category": "Pricing", "claim": "Subscription", "source_url": "https://c.com/1"},
    ]

    result = verify_multi_source(findings, min_sources=2)
    assert result["verification_rate"] > 0
    assert len(result["verified_claims"]) >= 1
    assert len(result["unverified_claims"]) >= 1


def test_check_output_constraints_labels_claims():
    verified = check_output_constraints({
        "claim": "Has AI features",
        "confidence": 0.85,
        "source_url": "https://example.com",
        "is_company_claim": False,
    })
    assert verified["claim_type"] == "verified_fact"

    unverified = check_output_constraints({
        "claim": "Unknown pricing",
        "confidence": 0.3,
        "source_url": "",
    })
    assert unverified["claim_type"] == "unverified"
    assert "not publicly available" in unverified["claim"]


def test_should_escalate_low_confidence():
    state = {
        "findings": [{"confidence": 0.3, "source_url": "https://a.com"}],
        "tot_confidence": 0.2,
        "verification_results": {"verification_rate": 0.2},
        "missing_information": [],
        "iteration_count": 0,
        "errors": [],
        "recommendations": [],
    }

    result = should_escalate(state)
    assert result["requires_human_review"] is True
    assert len(result["escalation_reasons"]) > 0


def test_compute_evaluation_metrics():
    state = {
        "findings": [
            {
                "confidence": 0.9,
                "source_url": "https://a.com",
                "source_type": "official_website",
                "claim_type": "verified_fact",
                "published_date": "2025-01-01",
            },
        ],
        "categories": ["Products"],
        "companies": ["A", "B"],
        "category_completeness": {"Products": "complete"},
        "escalation": {"requires_human_review": False},
    }

    metrics = compute_evaluation_metrics(state)
    assert "correctness" in metrics
    assert "groundedness" in metrics
    assert "safety_compliance" in metrics
    assert metrics["findings_count"] == 1
