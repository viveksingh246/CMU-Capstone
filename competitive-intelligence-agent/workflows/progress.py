"""Workflow step labels and progress helpers for the UI pipeline tracker."""

from __future__ import annotations

from typing import Any, Callable

# Display order for the static pipeline overview (logical phases)
PIPELINE_PHASES: list[tuple[str, str]] = [
    ("intake", "Request validation & setup"),
    ("memory", "Historical context & coordination"),
    ("research", "Web research & knowledge indexing"),
    ("extraction", "Fact extraction & validation"),
    ("analysis", "Competitive analysis (ToT)"),
    ("governance", "Safety checks & human review"),
    ("delivery", "Report generation & archival"),
]

NODE_LABELS: dict[str, str] = {
    "parse_request": "Validate research request",
    "check_memory": "Load historical context",
    "coordinate": "Coordinate multi-agent workflow",
    "create_plan": "Build structured research plan",
    "search_sources": "Search & collect web sources",
    "index_rag": "Index documents for semantic retrieval",
    "extract_facts": "Extract structured facts from sources",
    "validate_evidence": "Validate evidence & apply guardrails",
    "check_completeness": "Assess research completeness",
    "compare_companies": "Analyze competitors (Tree-of-Thought)",
    "detect_changes": "Detect historical market changes",
    "safety_check": "Run safety & quality evaluation",
    "human_review_pause": "Pause for analyst review",
    "save_memory": "Persist run to intelligence archive",
    "generate_report": "Generate executive report",
}

NODE_PHASE: dict[str, str] = {
    "parse_request": "intake",
    "check_memory": "memory",
    "coordinate": "memory",
    "create_plan": "research",
    "search_sources": "research",
    "index_rag": "research",
    "extract_facts": "extraction",
    "validate_evidence": "extraction",
    "check_completeness": "extraction",
    "compare_companies": "analysis",
    "detect_changes": "analysis",
    "safety_check": "governance",
    "human_review_pause": "governance",
    "save_memory": "delivery",
    "generate_report": "delivery",
}

StepCallback = Callable[[str, str, dict[str, Any]], None]


def label_for_node(node_name: str, occurrence: int = 1) -> str:
    """Human-readable label; suffix pass number when a node repeats."""
    base = NODE_LABELS.get(node_name, node_name.replace("_", " ").title())
    if occurrence > 1 and node_name in {
        "search_sources",
        "extract_facts",
        "validate_evidence",
        "check_completeness",
        "coordinate",
    }:
        return f"{base} (pass {occurrence})"
    return base


def format_step_detail(node_name: str, update: dict[str, Any]) -> str:
    """Short status line from node output."""
    message = update.get("status_message")
    if message:
        return str(message)

    if node_name == "search_sources":
        docs = update.get("documents")
        if docs is not None:
            return f"{len(docs)} documents collected"
    if node_name == "extract_facts":
        findings = update.get("findings")
        if findings is not None:
            return f"{len(findings)} facts extracted"
    if node_name == "compare_companies":
        conf = update.get("tot_confidence")
        if conf is not None:
            return f"Analysis confidence {conf:.0%}"

    return "Step completed"


GROUPED_PHASES: list[tuple[str, str, str, frozenset[str]]] = [
    ("plan", "1", "Intake", frozenset({"intake", "memory"})),
    ("research", "2", "Research", frozenset({"research"})),
    ("extract", "3", "Validate", frozenset({"extraction"})),
    ("analyze", "4", "Analyze", frozenset({"analysis"})),
    ("deliver", "5", "Deliver", frozenset({"governance", "delivery"})),
]


def compute_grouped_phase_status(pipeline_steps: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    """Map pipeline nodes to five grouped phases for the horizontal phase rail."""
    if not pipeline_steps:
        return [{"id": g[0], "num": g[1], "title": g[2], "status": "pending"} for g in GROUPED_PHASES]

    def grouped_index_for_node(node: str) -> int:
        phase_key = NODE_PHASE.get(node, "")
        for index, (_, _, _, keys) in enumerate(GROUPED_PHASES):
            if phase_key in keys:
                return index
        return 0

    last_step = pipeline_steps[-1]
    last_idx = grouped_index_for_node(last_step.get("node", ""))
    last_status = last_step.get("status", "complete")

    statuses: list[dict[str, str]] = []
    for index, (phase_id, num, title, _) in enumerate(GROUPED_PHASES):
        if index < last_idx:
            status = "complete"
        elif index == last_idx:
            status = "active" if last_status == "active" else "complete"
        else:
            status = "pending"
        statuses.append({"id": phase_id, "num": num, "title": title, "status": status})

    return statuses
