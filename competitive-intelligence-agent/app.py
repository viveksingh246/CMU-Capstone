"""Competitive Intelligence — professional research dashboard."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.components import (
    handle_approve_finalize,
    handle_monitor,
    handle_run,
    render_about_panel,
    render_app_banner,
    render_empty_state,
    render_llm_config,
    render_memory_panel,
    render_pipeline_status_banner,
    render_results,
    render_scope_card,
    render_sidebar,
)
from ui.theme import inject_global_styles

st.set_page_config(
    page_title="Competitive Intelligence Research Agent",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_global_styles()
    if st.session_state.get("pipeline_running") and not (
        st.session_state.get("analysis_run_pending")
        or st.session_state.get("approve_finalize_pending")
    ):
        # Recover from interrupted runs (browser refresh / server restart mid-pipeline).
        st.session_state["pipeline_running"] = False

    llm_config = render_llm_config()
    config = render_sidebar()
    render_app_banner(llm_config)

    tab_workspace, tab_archive, tab_platform = st.tabs(
        ["Research Workspace", "Intelligence Archive", "Platform"]
    )

    with tab_workspace:
        render_pipeline_status_banner()

        if st.session_state.pop("approve_finalize_pending", False):
            handle_approve_finalize(config, llm_config)
            st.rerun()

        run_pending, monitor_button = render_scope_card(config, llm_config)

        if run_pending:
            handle_run(config, llm_config)
        if monitor_button:
            handle_monitor()

        if "last_result" in st.session_state:
            render_results(st.session_state["last_result"], config, llm_config)
        elif not run_pending:
            render_empty_state()

    with tab_archive:
        render_memory_panel()

    with tab_platform:
        render_about_panel()


if __name__ == "__main__":
    main()
