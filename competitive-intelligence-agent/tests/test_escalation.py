"""Tests for escalation and conflict detection (Checkpoint 6.1)."""

from safety.escalation import (
    compute_overall_confidence,
    detect_conflicts,
    format_escalation_summary,
    should_escalate,
)


def test_compute_overall_confidence_weighted():
    state = {
        "findings": [{"confidence": 0.8}, {"confidence": 0.6}],
        "tot_confidence": 0.7,
        "verification_results": {"verification_rate": 0.9},
    }
    confidence = compute_overall_confidence(state)
    assert 0.6 < confidence < 0.9


def test_compute_overall_confidence_empty_findings():
    assert compute_overall_confidence({"findings": []}) == 0.0


def test_detect_conflicts_finds_contradictions():
    findings = [
        {"company": "A", "category": "Pricing", "claim": "Pay per use", "source_url": "https://a.com"},
        {"company": "A", "category": "Pricing", "claim": "Flat rate", "source_url": "https://b.com"},
    ]
    conflicts = detect_conflicts(findings)
    assert len(conflicts) == 1
    assert len(conflicts[0]["claims"]) == 2


def test_detect_conflicts_ignores_matching_claims():
    findings = [
        {"company": "A", "category": "Pricing", "claim": "Same", "source_url": "https://a.com"},
        {"company": "A", "category": "Pricing", "claim": "Same", "source_url": "https://b.com"},
    ]
    assert detect_conflicts(findings) == []


def test_should_escalate_conflicting_evidence():
    state = {
        "findings": [
            {"company": "A", "category": "Pricing", "claim": "A", "confidence": 0.9, "source_url": "https://a.com"},
            {"company": "A", "category": "Pricing", "claim": "B", "confidence": 0.9, "source_url": "https://b.com"},
        ],
        "tot_confidence": 0.8,
        "verification_results": {"verification_rate": 0.8},
        "missing_information": [],
        "iteration_count": 0,
        "errors": [],
        "recommendations": [],
    }
    result = should_escalate(state)
    assert result["requires_human_review"] is True
    assert any("contradict" in r.lower() for r in result["escalation_reasons"])


def test_should_escalate_incomplete_evidence_at_max_iterations():
    state = {
        "findings": [{"confidence": 0.9, "source_url": "https://a.com"}],
        "tot_confidence": 0.8,
        "verification_results": {"verification_rate": 0.8},
        "missing_information": ["Pricing"],
        "iteration_count": 3,
        "errors": [],
        "recommendations": [],
    }
    result = should_escalate(state)
    assert any("incomplete" in r.lower() for r in result["escalation_reasons"])


def test_should_escalate_retrieval_failures():
    state = {
        "findings": [{"confidence": 0.9, "source_url": "https://a.com"}],
        "tot_confidence": 0.8,
        "verification_results": {"verification_rate": 0.8},
        "missing_information": [],
        "iteration_count": 0,
        "errors": ["Search failed for 'q1'", "Search failed for 'q2'", "Search failed for 'q3'"],
        "recommendations": [],
    }
    result = should_escalate(state)
    assert any("retrieval" in r.lower() for r in result["escalation_reasons"])


def test_should_not_escalate_high_confidence():
    state = {
        "findings": [{"confidence": 0.95, "source_url": "https://a.com", "company": "A", "category": "Products", "claim": "X"}],
        "tot_confidence": 0.85,
        "verification_results": {"verification_rate": 0.9, "unverified_claims": []},
        "missing_information": [],
        "iteration_count": 0,
        "errors": [],
        "recommendations": [],
    }
    result = should_escalate(state)
    assert result["requires_human_review"] is False


def test_format_escalation_summary_includes_reasons():
    escalation = {
        "requires_human_review": True,
        "overall_confidence": 0.45,
        "threshold": 0.70,
        "escalation_reasons": ["Overall confidence below threshold"],
        "conflicts": [{"key": "A:Pricing", "claims": ["X", "Y"]}],
    }
    summary = format_escalation_summary(escalation)
    assert "Human Review Required" in summary
    assert "45%" in summary
    assert "A:Pricing" in summary


def test_format_escalation_summary_empty_when_not_required():
    assert format_escalation_summary({"requires_human_review": False}) == ""
