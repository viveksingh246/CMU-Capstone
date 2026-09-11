"""Engagement overview, activity feed, and presentation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from reporting.pdf_export import export_pdf_filename
from ui.analysis_state import (
    can_approve_result,
    can_export_result,
    is_analysis_running,
    is_pending_human_review,
)
from ui.export_cache import get_export_pdf_bytes
from ui.recommendation_view import (
    build_recommendations_intro,
    recommendation_basis,
    recommendation_meta_line,
)
from ui.pipeline_view import render_horizontal_pipeline
from workflows.progress import GROUPED_PHASES, NODE_PHASE

PHASE_TITLE_BY_ID = {phase_id: title for phase_id, _, title, _ in GROUPED_PHASES}


def _format_timestamp(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return raw[:19]


def build_activity_events(
    result: dict[str, Any],
    pipeline_steps: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Merge ReAct trace, pipeline nodes, warnings, and escalations into one feed."""
    events: list[dict[str, Any]] = []
    order = 0

    for step in pipeline_steps or []:
        node = step.get("node", "")
        phase_id = NODE_PHASE.get(node, "intake")
        events.append(
            {
                "order": order,
                "kind": "step",
                "filter": "steps",
                "title": step.get("label", "Pipeline step"),
                "detail": step.get("detail", ""),
                "timestamp": "",
                "status": step.get("status", "complete"),
                "agent": PHASE_TITLE_BY_ID.get(
                    next((g[0] for g in GROUPED_PHASES if phase_id in g[3]), "plan"),
                    "Pipeline",
                ),
            }
        )
        order += 1

    stm = result.get("short_term_memory", {})
    for step in stm.get("reasoning_steps", []):
        events.append(
            {
                "order": order,
                "kind": "step",
                "filter": "steps",
                "title": step.get("action", "Agent action"),
                "detail": step.get("observation", ""),
                "timestamp": _format_timestamp(step.get("timestamp", "")),
                "status": "complete",
                "agent": step.get("phase", "agent").upper(),
            }
        )
        order += 1

    escalation = result.get("escalation", {})
    for reason in escalation.get("escalation_reasons", []):
        events.append(
            {
                "order": order,
                "kind": "escalation",
                "filter": "escalations",
                "title": "Escalation triggered",
                "detail": reason,
                "timestamp": "",
                "status": "escalation",
                "agent": "Governance",
            }
        )
        order += 1

    for conflict in escalation.get("conflicts", [])[:5]:
        events.append(
            {
                "order": order,
                "kind": "escalation",
                "filter": "escalations",
                "title": f"Conflicting evidence — {conflict.get('key', 'claim')}",
                "detail": f"{len(conflict.get('claims', []))} conflicting claims",
                "timestamp": "",
                "status": "escalation",
                "agent": "Validator",
            }
        )
        order += 1

    for error in result.get("errors", []):
        events.append(
            {
                "order": order,
                "kind": "warning",
                "filter": "warnings",
                "title": "Pipeline notice",
                "detail": error,
                "timestamp": "",
                "status": "warning",
                "agent": "System",
            }
        )
        order += 1

    findings = result.get("findings", [])
    for finding in findings[:12]:
        events.append(
            {
                "order": order,
                "kind": "finding",
                "filter": "findings",
                "title": f"{finding.get('company', 'Company')} · {finding.get('category', 'Category')}",
                "detail": (finding.get("claim") or "")[:160],
                "timestamp": finding.get("published_date") or "",
                "status": finding.get("claim_type", "verified_fact"),
                "agent": "Researcher",
            }
        )
        order += 1

    return events


def feed_counts(result: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "all": len(events),
        "findings": len(result.get("findings", [])),
        "steps": sum(1 for e in events if e["filter"] == "steps"),
        "escalations": sum(1 for e in events if e["filter"] == "escalations"),
        "warnings": sum(1 for e in events if e["filter"] == "warnings"),
    }


def _status_label(status: str) -> str:
    labels = {
        "complete": "Complete",
        "active": "In progress",
        "verified_fact": "Verified",
        "warning": "Notice",
        "escalation": "Escalation",
        "analytical_assessment": "Assessment",
        "company_statement": "Company claim",
        "unverified": "Unverified",
    }
    return labels.get(status, status.replace("_", " ").title())


def render_engagement_header(result: dict[str, Any], config: dict[str, Any]) -> None:
    companies = ", ".join(config.get("companies", []))
    industry = config.get("industry", "Research engagement")
    report_text = result.get("final_report", "")
    confidence = result.get("escalation", {}).get(
        "overall_confidence", result.get("tot_confidence", 0)
    )

    hdr_l, hdr_r = st.columns([4, 1])
    with hdr_l:
        with st.container(border=True):
            st.caption("Active engagement")
            st.subheader(industry)
            st.write(companies)
            status = result.get("status_message", "Analysis complete")
            if is_analysis_running():
                status = "Pipeline in progress"
            elif is_pending_human_review(result):
                status = "Awaiting analyst approval"
            st.caption(
                f"Confidence {confidence:.0%} · {len(result.get('findings', []))} findings · "
                f"{status}"
            )
    with hdr_r:
        export_ready = can_export_result(result)
        pdf_bytes = b""
        if export_ready:
            try:
                pdf_bytes = get_export_pdf_bytes(result, config)
                pdf_name = export_pdf_filename(config)
            except Exception:
                pdf_name = "competitive_intelligence_report.pdf"
        else:
            pdf_name = "competitive_intelligence_report.pdf"
        st.download_button(
            "Export PDF",
            data=pdf_bytes,
            file_name=pdf_name,
            mime="application/pdf",
            width="stretch",
            disabled=not export_ready,
            key="engagement_export_pdf",
        )
        if report_text:
            st.download_button(
                "Export Markdown",
                data=report_text,
                file_name="competitive_intelligence_report.md",
                mime="text/markdown",
                width="stretch",
                disabled=not export_ready,
                key="engagement_export_md",
            )


def render_phase_rail(pipeline_steps: list[dict[str, Any]] | None) -> None:
    render_horizontal_pipeline(pipeline_steps, running=False)


def render_top_recommendations(result: dict[str, Any], *, limit: int = 3) -> None:
    """Strategic recommendations shown directly below the analysis pipeline."""
    recommendations = result.get("recommendations", [])
    if not recommendations:
        return

    with st.container(border=True):
        st.markdown(
            '<p class="ci-pipeline-title">Top recommendations</p>',
            unsafe_allow_html=True,
        )
        st.caption(build_recommendations_intro(result))
        for rec in recommendations[:limit]:
            if not isinstance(rec, dict):
                continue
            with st.container(border=True):
                st.markdown(f"**{rec.get('recommendation', '')}**")
                st.caption(recommendation_meta_line(rec))
                basis = recommendation_basis(rec)
                if basis:
                    st.markdown(f"**Why this matters:** {basis}")
                else:
                    st.caption(
                        "Basis: derived from competitive scorecard, SWOT, and validated findings."
                    )


def render_filter_chips(counts: dict[str, int]) -> str:
    options = {
        "all": f"Everything {counts['all']}",
        "steps": f"Agent steps {counts['steps']}",
        "findings": f"Findings {counts['findings']}",
        "escalations": f"Escalations {counts['escalations']}",
        "warnings": f"Notices {counts['warnings']}",
    }
    return st.radio(
        "Activity filter",
        options=list(options.keys()),
        format_func=lambda key: options[key],
        horizontal=True,
        label_visibility="collapsed",
        key="activity_feed_filter",
    )


def render_activity_feed(events: list[dict[str, Any]], feed_filter: str) -> None:
    filtered = events if feed_filter == "all" else [e for e in events if e["filter"] == feed_filter]
    if not filtered:
        st.caption("No activity items for this filter.")
        return

    for event in filtered[:40]:
        with st.container(border=True):
            meta_l, meta_r = st.columns([3, 1])
            with meta_l:
                st.markdown(f"**{event.get('title', '')}**")
                if event.get("detail"):
                    st.caption(event.get("detail", ""))
            with meta_r:
                st.caption(event.get("agent", "Agent"))
                st.caption(_status_label(event.get("status", "info")))
                if event.get("timestamp"):
                    st.caption(event.get("timestamp", ""))


def render_comparison_table(title: str, data: dict[str, Any]) -> None:
    if not data:
        return

    st.markdown(f"**{title}**")
    if all(isinstance(v, str) for v in data.values()):
        frame = pd.DataFrame(
            [{"Company": company, "Summary": summary} for company, summary in data.items()]
        )
        st.dataframe(frame, width="stretch", hide_index=True)
        return

    if all(isinstance(v, dict) for v in data.values()):
        companies = list(data.keys())
        feature_keys: list[str] = []
        for company_data in data.values():
            if isinstance(company_data, dict):
                feature_keys.extend(company_data.keys())
        columns = sorted(set(feature_keys))
        if not columns:
            st.json(data)
            return

        rows = []
        for feature in columns:
            row = {"Feature": feature}
            for company in companies:
                row[company] = data.get(company, {}).get(feature, "—")
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        return

    st.json(data)


def render_overview_tab(
    result: dict[str, Any],
    config: dict[str, Any],
    pipeline_steps: list[dict[str, Any]] | None,
) -> None:
    tot = result.get("tot_analysis", {})
    hypothesis = result.get("selected_hypothesis") or tot.get("selected_hypothesis", "")

    if hypothesis:
        st.subheader("Selected hypothesis")
        with st.container(border=True):
            st.write(hypothesis)
            st.caption(f"ToT confidence {result.get('tot_confidence', 0):.0%}")

    events = build_activity_events(result, pipeline_steps)
    counts = feed_counts(result, events)
    st.subheader("Activity & agent trace")
    feed_filter = render_filter_chips(counts)
    render_activity_feed(events, feed_filter)
