"""Streamlit application for the Competitive Intelligence Research Agent."""

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from memory.database import CompetitiveIntelligenceDB
from visualizations.charts import (
    create_announcement_timeline,
    create_category_heatmap,
    create_completeness_chart,
    create_radar_chart,
    create_score_bar_chart,
)
from workflows.competitive_intelligence_graph import run_research

st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🔍",
    layout="wide",
)

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
}


def render_sidebar() -> dict:
    st.sidebar.header("Research Configuration")

    industry_presets = list(SAMPLE_COMPANIES.keys()) + ["Custom"]
    industry_choice = st.sidebar.selectbox("Industry Preset", industry_presets)

    if industry_choice == "Custom":
        industry = st.sidebar.text_input("Industry / Market", value="Cloud Data Platforms")
        default_companies = "Snowflake\nDatabricks\nGoogle BigQuery"
    else:
        industry = industry_choice
        default_companies = "\n".join(SAMPLE_COMPANIES[industry_choice])

    companies_text = st.sidebar.text_area(
        "Companies (one per line, 2-5 companies)",
        value=default_companies,
        height=100,
    )
    companies = [c.strip() for c in companies_text.split("\n") if c.strip()]

    categories = st.sidebar.multiselect(
        "Analysis Categories",
        DEFAULT_CATEGORIES,
        default=DEFAULT_CATEGORIES[:4],
    )

    date_range_days = st.sidebar.slider("Research Period (days)", 30, 365, 90)
    geographic_market = st.sidebar.text_input("Geographic Market", value="Global")
    report_depth = st.sidebar.selectbox("Report Depth", ["summary", "standard", "detailed"])
    include_historical = st.sidebar.checkbox("Include Historical Comparison", value=True)
    generate_alerts = st.sidebar.checkbox("Generate Alerts", value=True)

    st.sidebar.divider()
    api_status = []
    if settings.has_openai_api_key:
        api_status.append("✅ OpenAI API")
    else:
        api_status.append("❌ OpenAI API (required)")
    if settings.has_tavily_api_key:
        api_status.append("✅ Tavily Search")
    else:
        api_status.append("⚠️ Tavily Search (using sample data)")

    if settings.use_mcp:
        transport = settings.mcp_transport
        api_status.append(f"✅ MCP enabled ({transport})")
    else:
        api_status.append("⚠️ MCP disabled (direct tools)")

    st.sidebar.caption("API Status")
    for status in api_status:
        st.sidebar.write(status)

    return {
        "industry": industry,
        "companies": companies,
        "categories": categories,
        "date_range_days": date_range_days,
        "geographic_market": geographic_market,
        "report_depth": report_depth,
        "include_historical_comparison": include_historical,
        "generate_alerts": generate_alerts,
    }


def render_memory_panel():
    st.subheader("Research Memory")
    db = CompetitiveIntelligenceDB()

    with db._connect() as conn:
        runs = conn.execute(
            "SELECT run_id, research_topic, status, created_at FROM research_runs ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        alerts = conn.execute(
            """
            SELECT a.*, c.company_name
            FROM alerts a
            JOIN companies c ON a.company_id = c.company_id
            WHERE a.status = 'new'
            ORDER BY a.detected_at DESC
            LIMIT 10
            """
        ).fetchall()

    if runs:
        st.write("**Recent Research Runs**")
        for run in runs:
            st.caption(f"#{run['run_id']} — {run['research_topic']} ({run['status']}) — {run['created_at'][:10]}")
    else:
        st.info("No previous research runs. Run your first analysis to populate memory.")

    if alerts:
        st.write("**Active Alerts**")
        for alert in alerts:
            st.warning(f"**{alert['company_name']}** — {alert['alert_type']}: {alert['description']}")


def main():
    st.title("🔍 Competitive Intelligence Research Agent")
    st.markdown(
        "Autonomously research competitors, extract source-backed facts, "
        "compare companies, and generate executive reports."
    )

    config = render_sidebar()

    tab_research, tab_memory, tab_about = st.tabs(["Research", "Memory & Alerts", "About"])

    with tab_research:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Research Request")
            st.write(f"**Industry:** {config['industry']}")
            st.write(f"**Companies:** {', '.join(config['companies'])}")
            st.write(f"**Categories:** {', '.join(config['categories'])}")

        with col2:
            run_button = st.button("🚀 Start Research", type="primary", use_container_width=True)
            monitor_button = st.button("🔔 Run Monitoring Check", use_container_width=True)

        if run_button:
            if len(config["companies"]) < 2:
                st.error("Please enter at least 2 companies to compare.")
            elif not config["categories"]:
                st.error("Please select at least one analysis category.")
            elif not settings.has_openai_api_key:
                st.error("OPENAI_API_KEY is required. Copy .env.example to .env and add your key.")
            else:
                progress = st.progress(0, text="Initializing agent workflow...")
                status_box = st.empty()

                try:
                    status_box.info(
                        "Agent workflow: plan → search → RAG index → extract → validate → "
                        "ToT analyze → safety check → report"
                    )
                    progress.progress(20, text="Creating research plan...")

                    result = run_research(**config)

                    progress.progress(100, text="Research complete!")
                    st.session_state["last_result"] = result

                    if result.get("requires_human_review"):
                        status_box.warning(
                            "Research paused — human review required before report generation. "
                            "See the Human Review section below."
                        )
                    else:
                        status_box.success(result.get("status_message", "Research complete"))

                except Exception as exc:
                    st.error(f"Research failed: {exc}")
                    progress.empty()

        if monitor_button:
            st.info(
                "Monitoring check compares current memory against the latest findings. "
                "Run a full research first, then use this to detect changes."
            )
            if "last_result" in st.session_state:
                changes = st.session_state["last_result"].get("historical_changes", [])
                alerts = st.session_state["last_result"].get("alerts", [])
                if changes:
                    st.write("**Detected Changes:**")
                    for change in changes:
                        st.write(f"- **{change.get('company')}**: {change.get('description')}")
                if alerts:
                    st.write("**Alerts:**")
                    for alert in alerts:
                        st.warning(f"{alert.get('company')}: {alert.get('description')}")
                if not changes and not alerts:
                    st.success("No new changes detected since last analysis.")

        if "last_result" in st.session_state:
            result = st.session_state["last_result"]

            # Human review section (Checkpoint 6.1)
            if result.get("requires_human_review"):
                st.divider()
                st.subheader("Human Review Required")
                escalation = result.get("escalation", {})
                st.warning(
                    f"Overall confidence: **{escalation.get('overall_confidence', 0):.0%}** "
                    f"(threshold: {escalation.get('threshold', 0.7):.0%})"
                )
                for reason in escalation.get("escalation_reasons", []):
                    st.write(f"- {reason}")

                if result.get("escalation_summary"):
                    with st.expander("Escalation Details"):
                        st.markdown(result["escalation_summary"])

                approve_col, retry_col = st.columns(2)
                with approve_col:
                    if st.button("Approve & Generate Report", type="primary", use_container_width=True):
                        approved_result = run_research(**config, human_approved=True)
                        st.session_state["last_result"] = approved_result
                        st.rerun()
                with retry_col:
                    st.caption("Or adjust configuration and run research again.")

            st.divider()
            st.subheader("Executive Report")
            st.markdown(result.get("final_report", "No report generated."))

            scorecard = result.get("scorecard", [])
            findings = result.get("findings", [])
            completeness = result.get("category_completeness", {})

            st.divider()
            st.subheader("Visualizations")

            viz_cols = st.columns(3)
            charts = [
                ("Scorecard", create_score_bar_chart(scorecard)),
                ("Radar", create_radar_chart(scorecard)),
                ("Heatmap", create_category_heatmap(scorecard)),
            ]
            for col, (name, fig) in zip(viz_cols, charts):
                with col:
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

            timeline = create_announcement_timeline(findings)
            if timeline:
                st.plotly_chart(timeline, use_container_width=True)

            coverage = create_completeness_chart(completeness)
            if coverage:
                st.plotly_chart(coverage, use_container_width=True)

            # Evaluation metrics (Checkpoint 6.1)
            metrics = result.get("evaluation_metrics", {})
            if metrics:
                st.divider()
                st.subheader("Evaluation Metrics")
                metric_cols = st.columns(3)
                metric_items = [
                    ("Correctness", metrics.get("correctness", {})),
                    ("Groundedness", metrics.get("groundedness", {})),
                    ("Source Credibility", metrics.get("source_credibility", {})),
                    ("Freshness", metrics.get("freshness", {})),
                    ("Research Coverage", metrics.get("research_coverage", {})),
                    ("Safety Compliance", metrics.get("safety_compliance", {})),
                ]
                for col, (name, data) in zip(metric_cols * 2, metric_items):
                    with col:
                        if data:
                            status = "✅" if data.get("passed") else "⚠️"
                            st.metric(name, f"{data.get('value', 0):.0%}", delta=status)

            # ToT analysis summary (Checkpoint 4.1)
            tot = result.get("tot_analysis", {})
            if tot.get("selected_hypothesis"):
                with st.expander("Tree-of-Thought Analysis"):
                    st.write(f"**Selected Hypothesis:** {tot.get('selected_hypothesis')}")
                    st.write(f"**ToT Confidence:** {result.get('tot_confidence', 0):.0%}")
                    tree_meta = tot.get("tree_metadata", {})
                    if tree_meta.get("depths_explored"):
                        st.write(f"**Depths Explored:** {len(tree_meta['depths_explored'])}")

            # ReAct reasoning trace (Checkpoint 2.1)
            stm = result.get("short_term_memory", {})
            if stm.get("reasoning_steps"):
                with st.expander("ReAct Reasoning Trace"):
                    for step in stm["reasoning_steps"]:
                        st.caption(
                            f"**{step['phase'].upper()}** — {step['action']}: {step.get('observation', '')}"
                        )

            if result.get("errors"):
                with st.expander("Workflow Warnings"):
                    for error in result["errors"]:
                        st.warning(error)

            report_text = result.get("final_report", "")
            if report_text:
                st.download_button(
                    "📥 Download Report (Markdown)",
                    data=report_text,
                    file_name="competitive_intelligence_report.md",
                    mime="text/markdown",
                )

    with tab_memory:
        render_memory_panel()

    with tab_about:
        st.markdown(
            """
            ## About This Agent

            The **Competitive Intelligence Research Agent** is an agentic system that:

            1. **Plans** research based on your request
            2. **Searches** external sources (websites, news, docs)
            3. **Extracts** structured, source-backed facts
            4. **Validates** evidence quality and credibility
            5. **Checks completeness** and searches again when gaps exist
            6. **Compares** competitors with SWOT and scorecards
            7. **Remembers** previous findings in SQLite
            8. **Generates** executive reports with visualizations

            ### Agent Workflow (LangGraph + Multi-Agent)

            ```
            Parse Request → Check Memory → Coordinate
                  → Create Plan → Search Sources → RAG Index
                  → Extract Facts → Validate Evidence
                  → Check Completeness ── Missing? ──► Search again
                  → ToT Analysis → Detect Changes → Coordinate
                  → Safety Check ── Low confidence? ──► Human Review
                  → Save Memory → Generate Report
            ```

            ### Six Specialized Agents (Checkpoint 5.1)

            | Agent | Responsibility |
            |-------|---------------|
            | Planner | Structured research tasks and execution plans |
            | Researcher | RAG, web search, document collection |
            | Validator | Credibility, freshness, multi-source verification |
            | Analyst | Tree-of-Thought competitive comparison |
            | Reporter | Executive reports, SWOT, scorecards |
            | Coordinator | Shared context, memory, agent coordination |

            ### Architecture Checkpoints

            - **2.1** ReAct reasoning loop with short-term + long-term memory
            - **3.1** ChromaDB RAG with semantic retrieval
            - **4.1** Tree-of-Thought beam search with Critic evaluation
            - **5.1** Six-agent multi-agent coordination via LangGraph + MCP
            - **6.1** Safety guardrails, escalation, and human review

            ### Seven-Week Capstone Plan

            See `README.md` for the full implementation roadmap.

            ### Evaluation Targets

            - Research coverage: ≥ 90%
            - Citation coverage: ≥ 90%
            - Source quality (official/reputable): ≥ 70%
            - Extraction accuracy: ≥ 85%
            """
        )


if __name__ == "__main__":
    main()
