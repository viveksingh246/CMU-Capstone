"""Tests for LangGraph workflow routing and orchestration."""

from workflows.competitive_intelligence_graph import (
    build_graph,
    human_review_pause,
    parse_request,
    route_after_coordinate,
    route_after_parse,
    should_generate_report,
)


def test_build_graph_has_all_checkpoint_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())

    expected = {
        "parse_request",
        "check_memory",
        "coordinate",
        "create_plan",
        "search_sources",
        "index_rag",
        "extract_facts",
        "validate_evidence",
        "check_completeness",
        "compare_companies",
        "detect_changes",
        "safety_check",
        "human_review_pause",
        "save_memory",
        "generate_report",
    }
    assert expected.issubset(node_names)


def test_parse_request_valid_input():
    state = {
        "industry": "Cloud Data",
        "companies": ["Snowflake", "Databricks"],
        "categories": ["Products"],
        "date_range_days": 90,
        "errors": [],
    }
    result = parse_request(state)

    assert result["input_validated"] is True
    assert result["iteration_count"] == 0
    assert "short_term_memory" in result
    assert result["short_term_memory"]["step_count"] == 1


def test_parse_request_invalid_input_stops_workflow():
    state = {
        "industry": "Cloud Data",
        "companies": ["Snowflake"],
        "categories": ["Products"],
        "errors": [],
    }
    result = parse_request(state)

    assert result["input_validated"] is False
    assert len(result["errors"]) > 0
    assert route_after_parse(result) == "stop"


def test_parse_request_preserves_human_approved():
    state = {
        "industry": "Cloud Data",
        "companies": ["Snowflake", "Databricks"],
        "categories": ["Products"],
        "date_range_days": 90,
        "human_approved": True,
        "errors": [],
    }
    result = parse_request(state)
    assert result["human_approved"] is True


def test_route_after_coordinate_initial_phase():
    state = {"research_plan": None, "comparison": None}
    assert route_after_coordinate(state) == "create_plan"


def test_route_after_coordinate_post_analysis_phase():
    state = {"comparison": {"feature_matrix": {}}, "escalation": None}
    assert route_after_coordinate(state) == "safety_check"


def test_route_after_coordinate_empty_comparison_still_advances():
    """Empty comparison dict must not loop back to planning."""
    state = {"comparison": {}, "escalation": None}
    assert route_after_coordinate(state) == "safety_check"


def test_should_generate_report_requires_human_review():
    state = {"requires_human_review": True, "human_approved": False}
    assert should_generate_report(state) == "human_review"


def test_should_generate_report_proceeds_when_approved():
    state = {"requires_human_review": True, "human_approved": True}
    assert should_generate_report(state) == "generate"


def test_should_generate_report_proceeds_when_confident():
    state = {"requires_human_review": False, "human_approved": False}
    assert should_generate_report(state) == "generate"


def test_human_review_pause_sets_escalation_summary():
    state = {
        "escalation": {
            "requires_human_review": True,
            "overall_confidence": 0.45,
            "threshold": 0.70,
            "escalation_reasons": ["Overall confidence below threshold"],
            "conflicts": [],
        },
        "short_term_memory": {},
    }
    result = human_review_pause(state)

    assert "escalation_summary" in result
    assert "Human Review Required" in result["escalation_summary"]
    assert result["short_term_memory"]["step_count"] == 1
