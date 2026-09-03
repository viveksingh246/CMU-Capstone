"""Tests for research completeness checking."""

from agents.completeness import check_completeness, should_continue_research


def test_completeness_detects_missing_categories():
    state = {
        "categories": ["Products", "Pricing"],
        "companies": ["Snowflake", "Databricks"],
        "findings": [
            {"company": "Snowflake", "category": "Products", "claim": "Data warehouse"},
            {"company": "Databricks", "category": "Products", "claim": "Lakehouse"},
        ],
        "search_queries": [],
        "iteration_count": 0,
    }

    result = check_completeness(state)
    assert "Pricing" in result["missing_information"]
    assert result["iteration_count"] == 1


def test_should_continue_when_missing_and_under_max_iterations():
    state = {"missing_information": ["Pricing"], "iteration_count": 1}
    assert should_continue_research(state) == "search_more"


def test_should_analyze_when_complete():
    state = {"missing_information": [], "iteration_count": 1}
    assert should_continue_research(state) == "analyze"


def test_should_analyze_at_max_iterations():
    state = {"missing_information": ["Pricing"], "iteration_count": 3}
    assert should_continue_research(state) == "analyze"
