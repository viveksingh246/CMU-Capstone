"""LangGraph workflow for competitive intelligence research."""

from datetime import date, timedelta
from typing import Any

from langgraph.graph import END, StateGraph

from agents.analyst import analyze_competitors, detect_historical_changes
from agents.completeness import check_completeness, should_continue_research
from agents.coordinator import coordinate_pre_report, coordinate_workflow
from agents.extractor import extract_facts
from agents.memory_agent import check_memory, save_to_memory
from agents.planner import create_research_plan
from agents.reporter import generate_report
from agents.researcher import collect_research, index_documents_for_rag
from agents.validator import validate_evidence
from memory.short_term import record_react_step
from safety.escalation import format_escalation_summary
from safety.guardrails import InputValidationError, validate_research_request
from workflows.state import ResearchState


def parse_request(state: ResearchState) -> dict[str, Any]:
    """Initialize date range, validate input, and set workflow metadata."""
    try:
        validate_research_request(
            state.get("industry", ""),
            state.get("companies", []),
            state.get("categories", []),
        )
    except InputValidationError as exc:
        return {
            "input_validated": False,
            "errors": state.get("errors", []) + list(exc.violations),
            "status_message": f"Input validation failed: {exc}",
        }

    days = state.get("date_range_days", 90)
    end = date.today()
    start = end - timedelta(days=days)

    result = {
        "input_validated": True,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "iteration_count": 0,
        "documents": [],
        "findings": [],
        "completed_queries": [],
        "errors": [],
        "retrieved_context": [],
        "rag_chunks_indexed": 0,
        "human_approved": state.get("human_approved", False),
        "status_message": "Research request parsed and validated",
    }

    react = record_react_step(
        {**state, **result},
        "reason",
        "Interpret research objective",
        f"Compare {', '.join(state.get('companies', []))} in {state.get('industry', '')}",
    )
    result.update(react)
    return result


def coordinate(state: ResearchState) -> dict[str, Any]:
    """Memory & Coordination Agent node."""
    return coordinate_workflow(state)


def index_rag(state: ResearchState) -> dict[str, Any]:
    """Index collected documents into ChromaDB vector store."""
    return index_documents_for_rag(state)


def safety_check(state: ResearchState) -> dict[str, Any]:
    """Pre-report safety check: escalation and evaluation metrics."""
    return coordinate_pre_report(state)


def should_generate_report(state: ResearchState) -> str:
    """Route: generate report or pause for human review."""
    from config import settings

    if state.get("requires_human_review") and settings.require_human_approval:
        if not state.get("human_approved"):
            return "human_review"
    return "generate"


def human_review_pause(state: ResearchState) -> dict[str, Any]:
    """Pause workflow and prepare escalation summary for human reviewer."""
    escalation = state.get("escalation", {})
    summary = format_escalation_summary(escalation)

    react = record_react_step(
        state,
        "reflect",
        "Pause for human review",
        f"Reasons: {', '.join(escalation.get('escalation_reasons', []))}",
    )

    return {
        **react,
        "status_message": "Workflow paused — human review required",
        "escalation_summary": summary,
    }


def route_after_parse(state: ResearchState) -> str:
    """Stop workflow when input validation fails."""
    if state.get("input_validated") is False:
        return "stop"
    return "continue"


def route_after_coordinate(state: ResearchState) -> str:
    """Route coordinator output based on workflow phase."""
    if state.get("comparison") and not state.get("escalation"):
        return "safety_check"
    return "create_plan"


def build_graph() -> StateGraph:
    """Build the competitive intelligence LangGraph workflow."""
    graph = StateGraph(ResearchState)

    # Nodes — 6 specialized agents (Checkpoint 5.1)
    graph.add_node("parse_request", parse_request)
    graph.add_node("check_memory", check_memory)
    graph.add_node("coordinate", coordinate)
    graph.add_node("create_plan", create_research_plan)
    graph.add_node("search_sources", collect_research)
    graph.add_node("index_rag", index_rag)
    graph.add_node("extract_facts", extract_facts)
    graph.add_node("validate_evidence", validate_evidence)
    graph.add_node("check_completeness", check_completeness)
    graph.add_node("compare_companies", analyze_competitors)
    graph.add_node("detect_changes", detect_historical_changes)
    graph.add_node("safety_check", safety_check)
    graph.add_node("human_review_pause", human_review_pause)
    graph.add_node("save_memory", save_to_memory)
    graph.add_node("generate_report", generate_report)

    # Edges
    graph.set_entry_point("parse_request")
    graph.add_conditional_edges(
        "parse_request",
        route_after_parse,
        {
            "continue": "check_memory",
            "stop": END,
        },
    )
    graph.add_edge("check_memory", "coordinate")
    graph.add_conditional_edges(
        "coordinate",
        route_after_coordinate,
        {
            "create_plan": "create_plan",
            "safety_check": "safety_check",
        },
    )
    graph.add_edge("create_plan", "search_sources")
    graph.add_edge("search_sources", "index_rag")
    graph.add_edge("index_rag", "extract_facts")
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
    graph.add_edge("detect_changes", "coordinate")

    graph.add_conditional_edges(
        "safety_check",
        should_generate_report,
        {
            "human_review": "human_review_pause",
            "generate": "save_memory",
        },
    )

    graph.add_edge("human_review_pause", END)
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
    human_approved: bool = False,
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
        "human_approved": human_approved,
        "user_request": f"Compare {', '.join(companies)} in {industry}",
    }

    return workflow.invoke(initial_state)
