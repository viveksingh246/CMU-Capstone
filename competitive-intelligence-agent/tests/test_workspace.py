"""Tests for workspace overview and activity feed helpers."""

from ui.workspace import build_activity_events, feed_counts
from workflows.progress import compute_grouped_phase_status


def test_build_activity_events_includes_warnings_and_steps():
    result = {
        "errors": ["Filtered 2 low-confidence findings"],
        "escalation": {"escalation_reasons": ["Overall confidence below threshold"], "conflicts": []},
        "short_term_memory": {
            "reasoning_steps": [
                {
                    "phase": "reflect",
                    "action": "Validated findings",
                    "observation": "85% verification",
                    "timestamp": "2026-09-04T15:00:00+00:00",
                }
            ]
        },
        "findings": [{"company": "A", "category": "Products", "claim": "Launched new API"}],
    }
    pipeline = [{"node": "validate_evidence", "label": "Validate evidence", "detail": "ok", "status": "complete"}]

    events = build_activity_events(result, pipeline)
    kinds = {e["filter"] for e in events}

    assert "warnings" in kinds
    assert "escalations" in kinds
    assert "steps" in kinds
    assert "findings" in kinds


def test_feed_counts():
    result = {"findings": [{}, {}]}
    events = [
        {"filter": "steps"},
        {"filter": "warnings"},
        {"filter": "escalations"},
    ]
    counts = feed_counts(result, events)
    assert counts["findings"] == 2
    assert counts["warnings"] == 1
    assert counts["all"] == 3


def test_compute_grouped_phase_status_marks_completed_phases():
    pipeline = [
        {"node": "parse_request", "status": "complete"},
        {"node": "search_sources", "status": "complete"},
        {"node": "extract_facts", "status": "active"},
    ]
    phases = compute_grouped_phase_status(pipeline)
    by_id = {p["id"]: p["status"] for p in phases}
    assert by_id["plan"] == "complete"
    assert by_id["research"] == "complete"
    assert by_id["extract"] in {"active", "complete"}
