"""Memory & Coordination agent (Checkpoint 5.1)."""

from __future__ import annotations

from typing import Any

from memory.short_term import ShortTermMemory, record_react_step
from safety.escalation import should_escalate
from safety.metrics import compute_evaluation_metrics
from workflows.state import ResearchState


def coordinate_workflow(state: ResearchState) -> dict[str, Any]:
    """
    Memory & Coordination Agent: maintains shared context, workflow state,
    and agent coordination across the multi-agent pipeline.
    """
    stm_data = state.get("short_term_memory", {})
    memory = ShortTermMemory.from_dict(stm_data)

    if not memory._objective:
        memory.set_objective(state.get("user_request", ""))

    # Track agent coordination status
    agent_status = {
        "planner": "complete" if state.get("research_plan") else "pending",
        "researcher": "complete" if state.get("documents") else "pending",
        "validator": "complete" if state.get("verification_results") else "pending",
        "analyst": "complete" if state.get("comparison") else "pending",
        "reporter": "complete" if state.get("final_report") else "pending",
        "memory": "active",
    }

    memory.update_search_progress(
        documents_collected=len(state.get("documents", [])),
        findings_extracted=len(state.get("findings", [])),
        iteration=state.get("iteration_count", 0),
        queries_completed=len(state.get("completed_queries", [])),
        rag_chunks_indexed=state.get("rag_chunks_indexed", 0),
        rag_chunks_retrieved=len(state.get("retrieved_context", [])),
    )

    coordination = {
        "agent_status": agent_status,
        "workflow_phase": _determine_phase(state),
        "shared_context": {
            "companies": state.get("companies", []),
            "categories": state.get("categories", []),
            "run_id": state.get("run_id"),
        },
    }

    return {
        "short_term_memory": memory.to_dict(),
        "coordination": coordination,
        "status_message": f"Coordination: phase={coordination['workflow_phase']}",
    }


def coordinate_pre_report(state: ResearchState) -> dict[str, Any]:
    """Final coordination: escalation check and evaluation metrics."""
    escalation = should_escalate(state)
    metrics = compute_evaluation_metrics({**state, "escalation": escalation})

    result = record_react_step(
        state,
        "decide",
        "Evaluate escalation and quality metrics",
        f"confidence={escalation['overall_confidence']:.0%}, escalate={escalation['requires_human_review']}",
    )

    return {
        **result,
        "escalation": escalation,
        "evaluation_metrics": metrics,
        "requires_human_review": escalation["requires_human_review"],
        "status_message": (
            "Human review required before report generation"
            if escalation["requires_human_review"]
            else "Quality checks passed — proceeding to report"
        ),
    }


def _determine_phase(state: ResearchState) -> str:
    if state.get("final_report"):
        return "complete"
    if state.get("comparison"):
        return "analysis"
    if state.get("findings"):
        return "validation"
    if state.get("documents"):
        return "extraction"
    if state.get("search_queries"):
        return "research"
    if state.get("research_plan"):
        return "planning"
    return "initialization"
