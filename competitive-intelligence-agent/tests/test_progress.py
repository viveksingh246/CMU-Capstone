"""Tests for workflow progress labels and formatting."""

from workflows.progress import (
    NODE_LABELS,
    PIPELINE_PHASES,
    format_step_detail,
    label_for_node,
)


def test_all_graph_nodes_have_labels() -> None:
    expected_nodes = {
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
    assert expected_nodes == set(NODE_LABELS.keys())


def test_label_for_node_repeats_search_pass() -> None:
    assert label_for_node("search_sources", 1) == NODE_LABELS["search_sources"]
    assert "(pass 2)" in label_for_node("search_sources", 2)


def test_format_step_detail_prefers_status_message() -> None:
    detail = format_step_detail("extract_facts", {"status_message": "Extracted 12 facts"})
    assert detail == "Extracted 12 facts"


def test_format_step_detail_counts_documents() -> None:
    detail = format_step_detail("search_sources", {"documents": [{}, {}, {}]})
    assert detail == "3 documents collected"


def test_pipeline_phases_non_empty() -> None:
    assert len(PIPELINE_PHASES) >= 5
    assert all(phase_id and title for phase_id, title in PIPELINE_PHASES)
