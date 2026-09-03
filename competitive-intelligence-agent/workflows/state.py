"""LangGraph state definition for the competitive intelligence workflow."""

from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    # User input
    user_request: str
    industry: str
    companies: list[str]
    categories: list[str]
    date_range: dict[str, str]
    date_range_days: int
    geographic_market: str
    report_depth: str
    include_historical_comparison: bool
    generate_alerts: bool

    # Workflow metadata
    run_id: int
    company_ids: dict[str, int]
    status_message: str
    iteration_count: int

    # Planning
    research_plan: dict[str, Any]
    search_queries: list[str]
    completed_queries: list[str]

    # Collection
    documents: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    missing_information: list[str]
    category_completeness: dict[str, str]

    # Analysis
    comparison: dict[str, Any]
    swot_analysis: dict[str, Any]
    recommendations: list[dict[str, Any]]
    scorecard: list[dict[str, Any]]
    historical_changes: list[dict[str, Any]]
    alerts: list[dict[str, Any]]

    # Memory
    previous_findings: list[dict[str, Any]]
    short_term_memory: dict[str, Any]
    coordination: dict[str, Any]

    # RAG (Checkpoint 3.1)
    rag_chunks_indexed: int
    retrieved_context: list[dict[str, Any]]

    # Tree-of-Thought (Checkpoint 4.1)
    tot_analysis: dict[str, Any]
    tot_confidence: float
    selected_hypothesis: str

    # Safety (Checkpoint 6.1)
    verification_results: dict[str, Any]
    escalation: dict[str, Any]
    requires_human_review: bool
    evaluation_metrics: dict[str, Any]
    human_approved: bool

    # Output
    final_report: str
    report_data: dict[str, Any]
    errors: list[str]
