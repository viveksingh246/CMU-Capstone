"""Tests for Memory & Coordination Agent (Checkpoint 5.1)."""

from agents.coordinator import _determine_phase, coordinate_pre_report, coordinate_workflow


def test_coordinate_workflow_tracks_agent_status():
    state = {
        "user_request": "Compare Snowflake vs Databricks",
        "research_plan": {"tasks": []},
        "documents": [{"url": "https://example.com"}],
        "findings": [],
        "short_term_memory": {},
    }
    result = coordinate_workflow(state)

    assert result["coordination"]["agent_status"]["planner"] == "complete"
    assert result["coordination"]["agent_status"]["researcher"] == "complete"
    assert result["coordination"]["agent_status"]["validator"] == "pending"
    assert result["coordination"]["workflow_phase"] == "extraction"


def test_coordinate_workflow_updates_search_progress():
    state = {
        "user_request": "Test",
        "documents": [{"url": "a"}, {"url": "b"}],
        "findings": [{"claim": "x"}],
        "iteration_count": 1,
        "completed_queries": ["q1"],
        "rag_chunks_indexed": 5,
        "retrieved_context": [{"text": "chunk"}],
        "short_term_memory": {},
    }
    result = coordinate_workflow(state)
    progress = result["short_term_memory"]["search_progress"]

    assert progress["documents_collected"] == 2
    assert progress["findings_extracted"] == 1
    assert progress["rag_chunks_indexed"] == 5


def test_coordinate_pre_report_sets_escalation():
    state = {
        "findings": [{"confidence": 0.3, "source_url": "https://a.com"}],
        "tot_confidence": 0.2,
        "verification_results": {"verification_rate": 0.2, "unverified_claims": ["a"]},
        "missing_information": [],
        "iteration_count": 0,
        "errors": [],
        "recommendations": [],
        "short_term_memory": {},
    }
    result = coordinate_pre_report(state)

    assert result["requires_human_review"] is True
    assert "evaluation_metrics" in result
    assert result["short_term_memory"]["reasoning_steps"][-1]["phase"] == "decide"


def test_determine_phase_progression():
    assert _determine_phase({}) == "initialization"
    assert _determine_phase({"research_plan": {}}) == "planning"
    assert _determine_phase({"search_queries": ["q"]}) == "research"
    assert _determine_phase({"documents": [{}]}) == "extraction"
    assert _determine_phase({"findings": [{}]}) == "validation"
    assert _determine_phase({"comparison": {}}) == "analysis"
    assert _determine_phase({"final_report": "done"}) == "complete"
