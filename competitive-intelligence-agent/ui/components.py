"""Reusable UI components for the competitive intelligence dashboard."""

from __future__ import annotations

import streamlit as st

from agents.llm import (
    LLMConfig,
    PROVIDER_INFO,
    default_fast_mode_for_provider,
    get_effective_max_queries_per_pass,
    get_effective_max_research_iterations,
    llm_context,
    provider_status,
    resolve_fast_mode,
    validate_llm_ready,
)
from config import settings
from memory.database import CompetitiveIntelligenceDB
from ui.analysis_state import (
    can_approve_result,
    can_run_analysis,
    is_analysis_running,
    is_pending_human_review,
    request_approve_finalize,
    request_run_analysis,
    reset_workflow_lock,
)
from ui.html_utils import render_html
from ui.pipeline_view import render_horizontal_pipeline
from ui.recommendation_view import recommendation_basis, recommendation_meta_line
from ui.workspace import (
    render_comparison_table,
    render_engagement_header,
    render_overview_tab,
    render_phase_rail,
    render_top_recommendations,
)
from visualizations.charts import (
    create_announcement_timeline,
    create_category_heatmap,
    create_completeness_chart,
    create_radar_chart,
    create_score_bar_chart,
)
from workflows.competitive_intelligence_graph import run_research_with_progress
from workflows.progress import label_for_node

DEFAULT_CATEGORIES = [
    "Products",
    "Features",
    "Pricing",
    "AI capabilities",
    "Partnerships",
    "Hiring trends",
]

SAMPLE_COMPANIES = {
    "Cloud Data Platforms": ["Snowflake", "Databricks", "Google BigQuery"],
    "AI Platforms": ["OpenAI", "Anthropic", "Google Gemini"],
    "Observability": ["Datadog", "New Relic", "Dynatrace"],
    "Financial Industry": ["JPMorgan Chase", "Goldman Sachs", "Visa"],
    "Education Industry": ["Coursera", "Udemy", "Instructure"],
}


def status_badges_html(llm_config: LLMConfig) -> str:
    status = provider_status(llm_config)
    provider_cls = "ci-badge-ok" if status["ready"] else "ci-badge-err"
    badges = [f'<span class="ci-badge {provider_cls}">{status["provider"]}</span>']
    badges.append(f'<span class="ci-badge ci-badge-ok">{status["model"]}</span>')
    if settings.has_tavily_api_key:
        badges.append('<span class="ci-badge ci-badge-ok">Live Search</span>')
    else:
        badges.append('<span class="ci-badge ci-badge-warn">Demo Data</span>')
    if resolve_fast_mode(llm_config):
        badges.append('<span class="ci-badge ci-badge-ok">Fast Mode</span>')
    else:
        badges.append('<span class="ci-badge ci-badge-warn">Full Mode</span>')
    return " ".join(badges)


def ci_logo_markup(size_class: str = "ci-logo-banner") -> str:
    """Branded CI monogram with intelligence radar motif."""
    return (
        f'<div class="ci-logo {size_class}" aria-label="Competitive Intelligence">'
        f'<svg class="ci-logo-svg" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" role="img">'
        f'<defs>'
        f'<linearGradient id="ciLogoGrad" x1="6" y1="4" x2="38" y2="40" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="#FFE9A8"/><stop offset="0.45" stop-color="#F5B041"/>'
        f'<stop offset="1" stop-color="#B8860B"/>'
        f"</linearGradient>"
        f'<linearGradient id="ciLogoShine" x1="0" y1="0" x2="0" y2="44" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="#FFFFFF" stop-opacity="0.35"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>'
        f"</linearGradient>"
        f"</defs>"
        f'<rect width="44" height="44" rx="11" fill="url(#ciLogoGrad)"/>'
        f'<rect width="44" height="44" rx="11" fill="url(#ciLogoShine)"/>'
        f'<circle cx="22" cy="22" r="15" fill="none" stroke="#3D2914" stroke-width="1" opacity="0.18"/>'
        f'<circle cx="22" cy="22" r="10.5" fill="none" stroke="#3D2914" stroke-width="1" opacity="0.22"/>'
        f'<path d="M22 22 L31 13" stroke="#7A1010" stroke-width="2" stroke-linecap="round"/>'
        f'<circle cx="22" cy="22" r="2.8" fill="#7A1010"/>'
        f'<circle cx="31" cy="13" r="2" fill="#3D2914"/>'
        f'<text x="22" y="36.5" text-anchor="middle" font-family="Inter,Arial,sans-serif" '
        f'font-size="11.5" font-weight="800" letter-spacing="0.04em" fill="#3D2914">CI</text>'
        f"</svg></div>"
    )


def build_app_banner_markup(llm_config: LLMConfig) -> str:
    badges = status_badges_html(llm_config)
    return (
        f'<div class="ci-sticky-banner" role="banner">'
        f'<div class="ci-sticky-banner-inner">'
        f'<div class="ci-sticky-brand">'
        f"{ci_logo_markup()}"
        f'<div class="ci-sticky-titles">'
        f'<p class="ci-sticky-product-title">Competitive Intelligence Research Agent</p>'
        f'<p class="ci-sticky-product-sub">Evidence-backed market analysis &amp; executive briefings</p>'
        f"</div></div>"
        f'<div class="ci-sticky-badges">{badges}</div>'
        f"</div></div>"
    )


def render_app_banner(llm_config: LLMConfig) -> None:
    """Fixed top banner with project title; stays visible while scrolling."""
    render_html(build_app_banner_markup(llm_config))


def render_llm_config() -> LLMConfig:
    provider_keys = list(PROVIDER_INFO.keys())
    default_provider = st.session_state.get("llm_provider", settings.llm_provider)
    if default_provider not in provider_keys:
        default_provider = "ollama"

    with st.sidebar:
        st.markdown('<p class="ci-sidebar-section">Intelligence Engine</p>', unsafe_allow_html=True)
        provider = st.selectbox(
            "Provider",
            provider_keys,
            index=provider_keys.index(default_provider),
            format_func=lambda p: PROVIDER_INFO[p]["label"],
            key="llm_provider_select",
        )
        st.session_state["llm_provider"] = provider

        default_model = settings.get_model_for_provider(provider)
        model = st.text_input(
            "Model",
            value=st.session_state.get(f"llm_model_{provider}", default_model),
            help=f"Default: {default_model}",
            key=f"llm_model_input_{provider}",
        )
        st.session_state[f"llm_model_{provider}"] = model

        if "fast_mode_enabled" not in st.session_state:
            st.session_state["fast_mode_enabled"] = default_fast_mode_for_provider(provider)

        fast_cb, fast_label = st.columns([0.12, 0.88], vertical_alignment="center")
        with fast_cb:
            st.session_state["fast_mode_enabled"] = st.checkbox(
                "Fast Mode",
                value=st.session_state["fast_mode_enabled"],
                help=(
                    "Fewer LLM calls, shorter research loops, and template reports when needed. "
                    "Turn off for deeper analysis (slower, more thorough)."
                ),
                label_visibility="collapsed",
                key="fast_mode_checkbox",
            )
        with fast_label:
            st.markdown(
                '<p class="ci-sidebar-checkbox-label ci-sidebar-checkbox-inline">Fast Mode</p>',
                unsafe_allow_html=True,
            )

        llm_config = LLMConfig.from_inputs(
            provider=provider,
            model=model,
            fast_mode=st.session_state["fast_mode_enabled"],
        )
        status = provider_status(llm_config)
        if status["ready"]:
            st.caption(f"● Online — {status['model']}")
        else:
            st.warning(status.get("message") or PROVIDER_INFO[provider]["hint"])

        st.divider()
        st.markdown('<p class="ci-sidebar-section">Workflow</p>', unsafe_allow_html=True)
        if st.button("Reset workflow lock", width="stretch", help="Use if buttons stay disabled after a failed or interrupted run"):
            reset_workflow_lock()
            st.rerun()

        st.divider()
        st.markdown('<p class="ci-sidebar-section">Governance</p>', unsafe_allow_html=True)
        approve_cb, approve_label = st.columns([0.12, 0.88], vertical_alignment="center")
        with approve_cb:
            st.session_state["human_approved"] = st.checkbox(
                "Pre-approve report",
                value=st.session_state.get("human_approved", False),
                help="Skip human-review pause when confidence is below threshold",
                label_visibility="collapsed",
                key="human_approved_checkbox",
            )
        with approve_label:
            st.markdown(
                '<p class="ci-sidebar-checkbox-label ci-sidebar-checkbox-inline">Pre-approve report</p>',
                unsafe_allow_html=True,
            )

    return llm_config


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown('<p class="ci-sidebar-section">Research Scope</p>', unsafe_allow_html=True)

        industry_presets = list(SAMPLE_COMPANIES.keys()) + ["Custom"]
        industry_choice = st.selectbox("Market vertical", industry_presets)

        if industry_choice == "Custom":
            industry = st.text_input("Market name", value="Cloud Data Platforms")
            default_companies = "Snowflake\nDatabricks\nGoogle BigQuery"
        else:
            industry = industry_choice
            default_companies = "\n".join(SAMPLE_COMPANIES[industry_choice])

        companies_text = st.text_area(
            "Companies (2–5)",
            value=default_companies,
            height=88,
            key=f"companies_text_{industry_choice}",
        )
        companies = [c.strip() for c in companies_text.split("\n") if c.strip()]

        categories = st.multiselect(
            "Analysis dimensions",
            DEFAULT_CATEGORIES,
            default=DEFAULT_CATEGORIES[:3],
        )

        c1, c2 = st.columns(2)
        with c1:
            date_range_days = st.selectbox(
                "Period",
                [30, 60, 90, 180, 365],
                index=1,
                format_func=lambda d: f"{d} days",
            )
        with c2:
            report_depth = st.selectbox("Depth", ["summary", "standard", "detailed"], index=0)

        geographic_market = st.text_input("Geography", value="Global")

        o1, o2 = st.columns(2)
        with o1:
            st.markdown(
                '<p class="ci-sidebar-checkbox-label">Historical diff</p>',
                unsafe_allow_html=True,
            )
            include_historical = st.checkbox(
                "Historical diff",
                value=True,
                label_visibility="collapsed",
                key="include_historical_checkbox",
            )
        with o2:
            st.markdown(
                '<p class="ci-sidebar-checkbox-label">Change alerts</p>',
                unsafe_allow_html=True,
            )
            generate_alerts = st.checkbox(
                "Change alerts",
                value=True,
                label_visibility="collapsed",
                key="generate_alerts_checkbox",
            )

    return {
        "industry": industry,
        "companies": companies,
        "categories": categories,
        "date_range_days": date_range_days,
        "geographic_market": geographic_market,
        "report_depth": report_depth,
        "include_historical_comparison": include_historical,
        "generate_alerts": generate_alerts,
        "human_approved": st.session_state.get("human_approved", False),
    }


def render_pipeline_status_banner() -> None:
    """Show when a long-running workflow is active so the UI does not look frozen."""
    if not is_analysis_running():
        return
    if st.session_state.get("approve_finalize_pending") or st.session_state.get("pipeline_running"):
        message = (
            "Finalizing the executive report — this re-runs the full pipeline and can take "
            "several minutes on Ollama or when API quotas are retrying. "
            "Check the terminal only for real errors (Traceback / 429)."
        )
    else:
        message = (
            "Analysis queued — starting intelligence pipeline. "
            "Large models may take several minutes per step."
        )
    st.info(message)


def render_scope_card(config: dict, llm_config: LLMConfig) -> tuple[bool, bool]:
    chips = "".join(f'<span class="ci-chip">{c}</span>' for c in config["companies"])
    cat_chips = "".join(f'<span class="ci-chip ci-chip-muted">{c}</span>' for c in config["categories"])
    with llm_context(llm_config):
        if resolve_fast_mode(llm_config):
            engine_mode = (
                f"fast · {get_effective_max_research_iterations()} research pass · "
                f"{get_effective_max_queries_per_pass()} queries/pass"
            )
        else:
            engine_mode = f"full · {settings.max_research_iterations} research passes · 5 queries/pass"

    render_html(
        f"""
        <div class="ci-scope-card">
          <div class="ci-scope-label">Active research brief</div>
          <p class="ci-scope-title">{config["industry"]}</p>
          <div class="ci-chip-row">{chips}</div>
          <div class="ci-chip-row">{cat_chips}</div>
          <p class="ci-meta">{config["date_range_days"]}d window · {config["report_depth"]} depth · {config["geographic_market"]} · {engine_mode}</p>
        </div>
        """
    )

    c1, c2 = st.columns([3, 3])
    with c1:
        if is_analysis_running():
            st.caption("Analysis in progress — controls re-enable when the pipeline completes or fails.")
        else:
            st.caption("Configure scope in the sidebar, then launch intelligence gathering.")
    with c2:
        b1, b2 = st.columns(2)
        with b1:
            st.button(
                "Run Analysis",
                type="primary",
                width="stretch",
                disabled=not can_run_analysis(),
                on_click=request_run_analysis,
                key="run_analysis_btn",
            )
        with b2:
            monitor_button = st.button(
                "Monitor Changes",
                width="stretch",
                disabled=is_analysis_running(),
            )
    return st.session_state.pop("analysis_run_pending", False), monitor_button


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="ci-empty">
          <h3>Launch your first competitive brief</h3>
          <p>Configure companies and analysis dimensions in the sidebar, then run a multi-agent
          research pipeline with live search, validation, and executive reporting.</p>
          <div class="ci-steps">
            <div class="ci-step">
              <div class="ci-step-num">1</div>
              <div class="ci-step-title">Define scope</div>
              <div class="ci-step-desc">Pick market, competitors &amp; categories</div>
            </div>
            <div class="ci-step">
              <div class="ci-step-num">2</div>
              <div class="ci-step-title">Gather evidence</div>
              <div class="ci-step-desc">Search, extract &amp; validate sources</div>
            </div>
            <div class="ci-step">
              <div class="ci-step-num">3</div>
              <div class="ci-step-title">Executive brief</div>
              <div class="ci-step-desc">Scorecard, matrix &amp; strategic insights</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_strip(metrics: dict, result: dict) -> None:
    if not metrics and not result:
        return

    escalation = result.get("escalation", {})
    items = [
        ("Confidence", f"{escalation.get('overall_confidence', result.get('tot_confidence', 0)):.0%}"),
        ("Findings", str(len(result.get("findings", [])))),
        ("Sources", str(len({f.get('source_url') for f in result.get('findings', []) if f.get('source_url')}))),
        ("Correctness", f"{metrics.get('correctness', {}).get('value', 0):.0%}" if metrics else "—"),
        ("Groundedness", f"{metrics.get('groundedness', {}).get('value', 0):.0%}" if metrics else "—"),
        ("Coverage", f"{metrics.get('research_coverage', {}).get('value', 0):.0%}" if metrics else "—"),
    ]

    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


def render_pipeline_progress(steps: list[dict] | None, *, running: bool = False) -> None:
    """Show grouped workflow phases horizontally with a blinking active indicator."""
    render_horizontal_pipeline(steps, running=running)


def _run_with_pipeline(
    config: dict,
    llm_config: LLMConfig,
    *,
    human_approved: bool | None = None,
    progress_slot=None,
) -> dict:
    """Run research with live step updates; persist steps to session state."""
    progress_slot = progress_slot if progress_slot is not None else st.empty()
    steps: list[dict] = []
    node_counts: dict[str, int] = {}

    run_config = dict(config)
    if human_approved is not None:
        run_config["human_approved"] = human_approved

    st.session_state["pipeline_running"] = True
    st.session_state["pipeline_steps"] = steps

    def on_step(node_name: str, detail: str, _update: dict) -> None:
        for step in steps:
            if step.get("status") == "active":
                step["status"] = "complete"

        node_counts[node_name] = node_counts.get(node_name, 0) + 1
        label = label_for_node(node_name, node_counts[node_name])
        steps.append(
            {
                "node": node_name,
                "label": label,
                "detail": detail,
                "status": "active",
            }
        )
        st.session_state["pipeline_steps"] = list(steps)
        with progress_slot.container():
            render_pipeline_progress(steps, running=True)

    try:
        result = run_research_with_progress(
            on_step,
            **run_config,
            llm_provider=llm_config.provider,
            llm_model=llm_config.model,
        )
    finally:
        for step in steps:
            if step.get("status") == "active":
                step["status"] = "complete"
        st.session_state["pipeline_running"] = False
        st.session_state["pipeline_steps"] = list(steps)
        progress_slot.empty()

    return result


def render_human_review(result: dict, config: dict, llm_config: LLMConfig) -> None:
    if is_analysis_running():
        st.info("Finalizing executive report — approval controls are locked until completion.")
        return
    if not is_pending_human_review(result):
        return

    escalation = result.get("escalation", {})
    reasons = escalation.get("escalation_reasons", [])
    reason_text = " · ".join(reasons) if reasons else "Confidence below governance threshold"
    confidence = escalation.get("overall_confidence", 0)
    with st.container(border=True):
        action_l, action_m, action_r = st.columns([5, 1.2, 1.8], vertical_alignment="center")
        with action_l:
            st.markdown("**Analyst review required**")
            st.caption(
                f"{reason_text}. Approve to finalize the executive report, "
                "or adjust scope in the sidebar and re-run."
            )
        with action_m:
            st.metric("Confidence", f"{confidence:.0%}")
        with action_r:
            st.button(
                "Approve & Finalize",
                type="primary",
                width="stretch",
                disabled=not can_approve_result(result),
                on_click=request_approve_finalize,
                key="approve_finalize_btn",
            )

    if result.get("escalation_summary"):
        with st.expander("Escalation details"):
            st.markdown(result["escalation_summary"])


def render_recommendations(recommendations: list) -> None:
    if not recommendations:
        return
    st.subheader("Strategic recommendations")
    for rec in recommendations[:6]:
        if not isinstance(rec, dict):
            continue
        with st.container(border=True):
            st.markdown(f"**{rec.get('recommendation', '')}**")
            st.caption(recommendation_meta_line(rec))
            basis = recommendation_basis(rec)
            if basis:
                st.markdown(f"**Why this matters:** {basis}")


def render_charts(result: dict) -> None:
    scorecard = result.get("scorecard", [])
    findings = result.get("findings", [])
    completeness = result.get("category_completeness", {})

    st.subheader("Competitive analytics")
    row1 = st.columns(3)
    charts = [
        create_score_bar_chart(scorecard),
        create_radar_chart(scorecard),
        create_category_heatmap(scorecard),
    ]
    for col, fig in zip(row1, charts):
        with col:
            if fig:
                with st.container(border=True):
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    row2 = st.columns(2)
    timeline = create_announcement_timeline(findings)
    coverage = create_completeness_chart(completeness)
    with row2[0]:
        if timeline:
            with st.container(border=True):
                st.plotly_chart(timeline, use_container_width=True, config={"displayModeBar": False})
    with row2[1]:
        if coverage:
            with st.container(border=True):
                st.plotly_chart(coverage, use_container_width=True, config={"displayModeBar": False})


def render_diagnostics(result: dict) -> None:
    tot = result.get("tot_analysis", {})
    stm = result.get("short_term_memory", {})
    has_content = bool(tot.get("selected_hypothesis") or stm.get("reasoning_steps") or result.get("errors"))
    if not has_content:
        return

    with st.expander("Agent trace & diagnostics", expanded=False):
        if tot.get("selected_hypothesis"):
            st.markdown(f"**ToT hypothesis** ({result.get('tot_confidence', 0):.0%} confidence)")
            st.write(tot.get("selected_hypothesis", ""))
        if stm.get("reasoning_steps"):
            st.markdown(f"**ReAct trace** — {stm.get('step_count', 0)} steps")
            for step in stm.get("reasoning_steps", [])[-8:]:
                st.text(f"{step['phase'].upper():8}  {step['action']}")
        for error in result.get("errors", []):
            st.warning(error)


def render_memory_panel() -> None:
    db = CompetitiveIntelligenceDB()
    with db._connect() as conn:
        runs = conn.execute(
            "SELECT run_id, research_topic, status, created_at FROM research_runs "
            "ORDER BY created_at DESC LIMIT 8"
        ).fetchall()
        alerts = conn.execute(
            """
            SELECT a.*, c.company_name
            FROM alerts a JOIN companies c ON a.company_id = c.company_id
            WHERE a.status = 'new' ORDER BY a.detected_at DESC LIMIT 10
            """
        ).fetchall()

    st.markdown('<div class="ci-section">Research archive</div>', unsafe_allow_html=True)
    if runs:
        for run in runs:
            st.markdown(
                f"""
                <div class="ci-run-row">
                  <span><span class="ci-run-id">#{run['run_id']}</span> {run['research_topic'][:55]}</span>
                  <span class="ci-run-date">{run['created_at'][:10]} · {run['status']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No archived research runs yet.")

    if alerts:
        st.markdown('<div class="ci-section">Active alerts</div>', unsafe_allow_html=True)
        for alert in alerts:
            st.markdown(
                f"""
                <div class="ci-cap-card" style="margin-bottom:0.4rem;">
                  <p class="ci-cap-title">{alert['company_name']} — {alert['alert_type']}</p>
                  <p class="ci-cap-desc">{alert['description'][:120]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_about_panel() -> None:
    st.markdown(
        """
        <div class="ci-cap-grid">
          <div class="ci-cap-card">
            <p class="ci-cap-title">Multi-agent pipeline</p>
            <p class="ci-cap-desc">Planner → Researcher → Validator → Analyst (ToT) → Reporter with coordinated memory.</p>
          </div>
          <div class="ci-cap-card">
            <p class="ci-cap-title">Evidence governance</p>
            <p class="ci-cap-desc">Source validation, multi-source verification, escalation &amp; human-in-the-loop approval.</p>
          </div>
          <div class="ci-cap-card">
            <p class="ci-cap-title">Flexible intelligence engine</p>
            <p class="ci-cap-desc">Ollama (local), Groq, Google Gemini, or OpenAI — switch per session in the sidebar.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("See README.md and docs/Capstone-Checkpoints-Implementation.md for architecture details.")


def handle_approve_finalize(config: dict, llm_config: LLMConfig) -> None:
    progress_slot = st.empty()
    st.session_state["pipeline_running"] = True
    try:
        with st.spinner("Finalizing executive report after analyst approval..."):
            approved = _run_with_pipeline(
                config,
                llm_config,
                human_approved=True,
                progress_slot=progress_slot,
            )
            approved["human_approved"] = True
            st.session_state["last_result"] = approved
            st.success(approved.get("status_message", "Executive brief finalized."))
    except Exception as exc:
        st.error(_pipeline_error_message(exc))
    finally:
        st.session_state["pipeline_running"] = False


def _pipeline_error_message(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "429" in message or "resourceexhausted" in lowered or "quota" in lowered:
        return (
            "LLM API quota exceeded. For Google Gemini free tier the limit is "
            "~20 requests/day per model. Switch provider to Ollama or Groq in the "
            "sidebar, enable Fast Mode, or wait for quota to reset."
        )
    return f"Pipeline failed: {exc}"


def handle_run(config: dict, llm_config: LLMConfig) -> None:
    def _abort_run(message: str) -> None:
        st.session_state["pipeline_running"] = False
        st.error(message)

    if len(config["companies"]) < 2:
        _abort_run("Select at least 2 companies for competitive comparison.")
        return
    if not config["categories"]:
        _abort_run("Select at least one analysis dimension.")
        return

    ready, err_msg = validate_llm_ready(llm_config)
    if not ready:
        _abort_run(err_msg)
        return

    st.session_state["pipeline_running"] = True
    try:
        with st.spinner(f"Intelligence pipeline running · {llm_config.provider}/{llm_config.model}"):
            st.session_state.pop("pipeline_steps", None)
            result = _run_with_pipeline(config, llm_config)
            st.session_state["last_result"] = result
            if is_pending_human_review(result):
                st.warning("Analysis complete — awaiting analyst approval.")
            else:
                st.success(result.get("status_message", "Executive brief ready."))
    except Exception as exc:
        st.error(_pipeline_error_message(exc))
    finally:
        st.session_state["pipeline_running"] = False


def handle_monitor() -> None:
    if "last_result" not in st.session_state:
        st.info("Run an analysis first to enable change monitoring.")
        return
    result = st.session_state["last_result"]
    changes = result.get("historical_changes", [])
    alerts = result.get("alerts", [])
    if not changes and not alerts:
        st.success("No material changes detected vs. prior research.")
        return
    for change in changes[:8]:
        st.markdown(
            f'<div class="ci-cap-card" style="margin-bottom:0.35rem;"><p class="ci-cap-desc"><strong>{change.get("company")}</strong> · {change.get("description", "")[:100]}</p></div>',
            unsafe_allow_html=True,
        )
    for alert in alerts[:5]:
        st.warning(f"{alert.get('company')}: {alert.get('description', '')[:80]}")


def render_results(result: dict, config: dict, llm_config: LLMConfig) -> None:
    render_human_review(result, config, llm_config)
    render_engagement_header(result, config)
    render_kpi_strip(result.get("evaluation_metrics", {}), result)

    pipeline_steps = st.session_state.get("pipeline_steps")
    render_phase_rail(pipeline_steps)
    render_top_recommendations(result)

    tab_overview, tab_brief, tab_matrix, tab_analytics, tab_trace = st.tabs(
        ["Overview", "Executive Brief", "Competitive Matrix", "Analytics", "Trace & Sources"]
    )

    with tab_overview:
        render_overview_tab(result, config, pipeline_steps)

    with tab_brief:
        report_text = result.get("final_report", "")
        st.subheader("Executive report")
        if report_text:
            with st.container(border=True):
                st.markdown("### Market Intelligence Brief")
                st.markdown(report_text)
        else:
            st.info("Report pending — approve review or re-run analysis.")

        render_recommendations(result.get("recommendations", []))

    with tab_matrix:
        comparison = result.get("comparison", {})
        render_comparison_table("Feature matrix", comparison.get("feature_matrix", {}))
        render_comparison_table("Pricing comparison", comparison.get("pricing_comparison", {}))
        swot = result.get("swot_analysis", {}).get("companies", [])
        if swot:
            st.markdown("**SWOT analysis**")
            for entry in swot:
                st.markdown(f"##### {entry.get('company', 'Company')}")
                for section in ("strengths", "weaknesses", "opportunities", "threats"):
                    points = entry.get(section, [])
                    if points:
                        st.caption(section.title())
                        for pt in points[:4]:
                            st.write(f"• {pt.get('point', '')}")

    with tab_analytics:
        render_charts(result)

    with tab_trace:
        render_diagnostics(result)
        findings = result.get("findings", [])
        if findings:
            st.subheader("Validated sources")
            seen: set[str] = set()
            for f in findings[:20]:
                url = f.get("source_url", "")
                if url and url not in seen:
                    seen.add(url)
                    st.markdown(f"- [{f.get('source_title', url)}]({url})")
