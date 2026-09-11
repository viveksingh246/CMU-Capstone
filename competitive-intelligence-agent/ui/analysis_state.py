"""Session-state helpers for analysis workflow button enablement."""

from __future__ import annotations

from typing import Any

import streamlit as st


def is_analysis_running() -> bool:
    return bool(
        st.session_state.get("pipeline_running", False)
        or st.session_state.get("analysis_run_pending", False)
        or st.session_state.get("approve_finalize_pending", False)
    )


def can_run_analysis() -> bool:
    return not is_analysis_running()


def is_pending_human_review(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    if not result.get("requires_human_review"):
        return False
    return not bool(result.get("human_approved"))


def can_approve_result(result: dict[str, Any] | None) -> bool:
    if not result or is_analysis_running():
        return False
    return is_pending_human_review(result)


def can_export_result(result: dict[str, Any] | None) -> bool:
    if not result or is_analysis_running():
        return False
    if is_pending_human_review(result):
        return False
    return bool(
        result.get("final_report")
        or result.get("findings")
        or result.get("scorecard")
        or result.get("comparison")
    )


def request_run_analysis() -> None:
    if not can_run_analysis():
        return
    st.session_state["analysis_run_pending"] = True


def request_approve_finalize() -> None:
    if is_analysis_running():
        return
    result = st.session_state.get("last_result")
    if not is_pending_human_review(result):
        return
    st.session_state["approve_finalize_pending"] = True
    st.session_state["pipeline_running"] = True


def reset_workflow_lock() -> None:
    """Clear stale in-progress flags when the UI is locked with no active run."""
    st.session_state["pipeline_running"] = False
    st.session_state.pop("analysis_run_pending", None)
    st.session_state.pop("approve_finalize_pending", None)
