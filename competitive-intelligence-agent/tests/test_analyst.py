"""Tests for Analysis Agent and historical change detection."""

from agents.analyst import _fallback_analysis, _sanitize_swot, detect_historical_changes


def test_detect_historical_changes_new_findings():
    state = {
        "include_historical_comparison": True,
        "generate_alerts": True,
        "previous_findings": [],
        "findings": [
            {
                "company": "Snowflake",
                "category": "pricing",
                "claim": "New pricing model",
                "source_url": "https://snowflake.com/pricing",
            }
        ],
    }
    result = detect_historical_changes(state)

    assert len(result["historical_changes"]) == 1
    assert result["historical_changes"][0]["change_type"] == "new_finding"
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["priority"] == "high"


def test_detect_historical_changes_pricing_update():
    state = {
        "include_historical_comparison": True,
        "generate_alerts": False,
        "previous_findings": [
            {"company": "Snowflake", "category": "Pricing", "claim": "Old pricing"},
        ],
        "findings": [
            {"company": "Snowflake", "category": "Pricing", "claim": "New pricing"},
        ],
    }
    result = detect_historical_changes(state)

    pricing_changes = [c for c in result["historical_changes"] if c["change_type"] == "pricing_change"]
    assert len(pricing_changes) == 1
    assert pricing_changes[0]["previous_value"] == "Old pricing"


def test_detect_historical_changes_disabled():
    state = {"include_historical_comparison": False}
    result = detect_historical_changes(state)
    assert result == {"historical_changes": [], "alerts": []}


def test_fallback_analysis_without_llm():
    state = {
        "findings": [{"claim": "test", "confidence": 0.8}],
        "short_term_memory": {},
    }
    tot_result = {
        "selected_hypothesis": "Snowflake leads in innovation",
        "tot_confidence": 0.72,
        "best_branch": {},
    }
    result = _fallback_analysis(
        state,
        companies=["Snowflake", "Databricks"],
        categories=["Products"],
        industry="Cloud Data",
        tot_result=tot_result,
    )

    assert result["selected_hypothesis"] == "Snowflake leads in innovation"
    assert len(result["scorecard"]) == 2
    assert result["comparison"]["ai_analysis"]["hypothesis"] == "Snowflake leads in innovation"
    assert "ToT fallback" in result["status_message"]


def test_sanitize_swot_strips_non_integer_evidence_ids():
    raw = [
        {
            "company": "Snowflake",
            "strengths": [{"point": "Strong platform", "evidence_ids": ["Snowflake Feature Matrix", 12]}],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }
    ]
    sanitized = _sanitize_swot(raw)
    assert sanitized[0]["strengths"][0]["evidence_ids"] == [12]
