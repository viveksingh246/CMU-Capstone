"""Memory persistence for research runs."""

from typing import Any

from tools.mcp_tools import get_previous_findings_mcp, save_research_run_mcp
from workflows.state import ResearchState


def check_memory(state: ResearchState) -> dict[str, Any]:
    """Load previous findings for requested companies."""
    previous_findings: list[dict[str, Any]] = []

    for company in state.get("companies", []):
        findings = get_previous_findings_mcp(company, limit=20)
        previous_findings.extend(findings)

    return {
        "previous_findings": previous_findings,
        "status_message": f"Loaded {len(previous_findings)} previous findings from memory",
    }


def save_to_memory(state: ResearchState) -> dict[str, Any]:
    """Persist research run, findings, scores, and alerts."""
    payload = {
        "industry": state.get("industry", ""),
        "companies": state.get("companies", []),
        "categories": state.get("categories", []),
        "date_range": state.get("date_range", {}),
        "run_id": state.get("run_id"),
        "findings": state.get("findings", []),
        "scorecard": state.get("scorecard", []),
        "alerts": state.get("alerts", []),
    }

    result = save_research_run_mcp(payload)

    return {
        "run_id": result.get("run_id"),
        "company_ids": result.get("company_ids", {}),
        "status_message": f"Saved research run #{result.get('run_id')} to memory",
    }
