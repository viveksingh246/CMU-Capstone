"""Streamlit gallery for capturing presentation screenshots."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.demo_result import (
    demo_config,
    demo_pipeline_active_steps,
    demo_pipeline_steps,
    demo_result,
)
from ui.components import (
    render_app_banner,
    render_empty_state,
    render_human_review,
    render_kpi_strip,
    render_llm_config,
    render_results,
    render_scope_card,
)
from ui.pipeline_view import render_horizontal_pipeline
from ui.theme import inject_global_styles

st.set_page_config(
    page_title="CI Agent — Screenshot Gallery",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

VIEW = st.query_params.get("view", "workspace")


def main() -> None:
    inject_global_styles()
    config = demo_config()
    llm_config = render_llm_config()
    render_app_banner(llm_config)

    with st.sidebar:
        st.markdown("**Industry preset**")
        st.selectbox("industry_preset", [config["industry"]], label_visibility="collapsed")
        st.markdown("**Competitors**")
        st.text_area("companies_input", "\n".join(config["companies"]), height=110, label_visibility="collapsed")
        st.markdown("**Analysis categories**")
        for cat in config["categories"]:
            st.checkbox(cat, value=True, disabled=True)
        st.markdown("**Research period**")
        st.slider("days", 30, 365, config["date_range_days"], label_visibility="collapsed")

    if VIEW == "workspace":
        st.markdown("### Research Workspace")
        render_scope_card(config, llm_config)
        render_empty_state()

    elif VIEW == "pipeline":
        st.session_state["pipeline_running"] = True
        st.markdown("### Analysis in Progress")
        render_horizontal_pipeline(demo_pipeline_active_steps())
        st.progress(42, text="Searching sources — Snowflake AI capabilities official documentation")

    elif VIEW == "results":
        st.session_state["pipeline_steps"] = demo_pipeline_steps()
        render_results(demo_result(requires_review=False), config, llm_config)

    elif VIEW == "human_review":
        render_human_review(demo_result(requires_review=True), config, llm_config)

    elif VIEW == "metrics":
        result = demo_result(requires_review=False)
        st.markdown("### Evaluation Metrics Dashboard")
        render_kpi_strip(result.get("evaluation_metrics", {}), result)
        st.markdown("#### ReAct Reasoning Trace")
        for entry in result.get("react_trace", []):
            st.markdown(f"**{entry['step'].upper()}** — {entry['thought']}")

    else:
        st.error(f"Unknown view: {VIEW}")


if __name__ == "__main__":
    main()
