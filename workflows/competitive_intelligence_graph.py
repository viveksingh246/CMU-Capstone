"""LangGraph workflow for competitive intelligence research."""

from datetime import date, timedelta
from typing import Any

from langgraph.graph import END, StateGraph

from agents.analyst import analyze_competitors, detect_historical_changes
from agents.completeness import check_completeness, should_continue_research
from agents.extractor import extract_facts
from agents.memory_agent import check_memory, save_to_memory
from agents.planner import create_research_plan
from agents.reporter import generate_report
from agents.researcher import collect_research
from agents.validator import validate_evidence
from workflows.state import ResearchState


def parse_request(state: ResearchState) -> dict[str, Any]:
    """Initialize date range and workflow metadata."""
    days = state.get("date_range_days", 90)
    end = date.today()
    start = end - timedelta(days=days)

    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "iteration_count": 0,
        "documents": [],
        "findings": [],
        "completed_queries": [],
        "errors": [],
        "status_message": "Research request parsed",
    }


def build_graph() -> StateGraph:
    """Build the competitive intelligence LangGraph workflow."""
    graph = StateGraph(ResearchState)

    # Nodes
    graph.add_node("parse_request", parse_request)
    graph.add_node("check_memory", check_memory)
    graph.add_node("create_plan", create_research_plan)
    graph.add_node("search_sources", collect_research)
    graph.add_node("extract_facts", extract_facts)
    graph.add_node("validate_evidence", validate_evidence)
    graph.add_node("check_completeness", check_completeness)
    graph.add_node("compare_companies", analyze_competitors)
    graph.add_node("detect_changes", detect_historical_changes)
    graph.add_node("save_memory", save_to_memory)
    graph.add_node("generate_report", generate_report)

    # Edges
    graph.set_entry_point("parse_request")
    graph.add_edge("parse_request", "check_memory")
    graph.add_edge("check_memory", "create_plan")
    graph.add_edge("create_plan", "search_sources")
    graph.add_edge("search_sources", "extract_facts")
    graph.add_edge("extract_facts", "validate_evidence")
    graph.add_edge("validate_evidence", "check_completeness")

    graph.add_conditional_edges(
        "check_completeness",
        should_continue_research,
        {
            "search_more": "search_sources",
            "analyze": "compare_companies",
        },
    )

    graph.add_edge("compare_companies", "detect_changes")
    graph.add_edge("detect_changes", "save_memory")
    graph.add_edge("save_memory", "generate_report")
    graph.add_edge("generate_report", END)

    return graph


def run_research(
    industry: str,
    companies: list[str],
    categories: list[str],
    date_range_days: int = 90,
    geographic_market: str = "Global",
    report_depth: str = "standard",
    include_historical_comparison: bool = True,
    generate_alerts: bool = True,
) -> ResearchState:
    """Execute the full competitive intelligence workflow."""
    workflow = build_graph().compile()

    initial_state: ResearchState = {
        "industry": industry,
        "companies": companies,
        "categories": categories,
        "date_range_days": date_range_days,
        "geographic_market": geographic_market,
        "report_depth": report_depth,
        "include_historical_comparison": include_historical_comparison,
        "generate_alerts": generate_alerts,
        "user_request": f"Compare {', '.join(companies)} in {industry}",
    }

    return workflow.invoke(initial_state)
