"""Horizontal analysis pipeline progress UI."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from workflows.progress import compute_grouped_phase_status


def get_current_step(steps: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Return the active step, or the most recent step when idle."""
    if not steps:
        return None
    for step in reversed(steps):
        if step.get("status") == "active":
            return step
    return steps[-1]


def _progress_percent(phases: list[dict[str, str]]) -> float:
    if not phases:
        return 0.0
    if len(phases) == 1:
        status = phases[0].get("status", "pending")
        if status == "complete":
            return 100.0
        if status == "active":
            return 55.0
        return 0.0

    for index, phase in enumerate(phases):
        if phase.get("status") == "active":
            return (index + 0.5) / (len(phases) - 1) * 100.0

    if all(phase.get("status") == "complete" for phase in phases):
        return 100.0

    last_complete = -1
    for index, phase in enumerate(phases):
        if phase.get("status") == "complete":
            last_complete = index
    if last_complete >= 0:
        return last_complete / (len(phases) - 1) * 100.0
    return 0.0


def _phase_markup(phase: dict[str, str]) -> str:
    status = phase.get("status", "pending")
    num = escape(str(phase.get("num", "")))
    title = escape(phase.get("title", ""))
    return (
        f'<div class="ci-h-phase ci-h-phase-{status}">'
        f'<div class="ci-h-dot-wrap"><span class="ci-h-dot" aria-hidden="true"></span></div>'
        f'<p class="ci-h-phase-num">{num}</p>'
        f'<p class="ci-h-phase-title">{title}</p>'
        f"</div>"
    )


def _progress_bar_markup(fill: float) -> str:
    return (
        f'<div class="ci-h-progress-bar" aria-hidden="true">'
        f'<div class="ci-h-progress-fill" style="width: {fill:.1f}%;"></div>'
        f"</div>"
    )


def _current_step_markup(current_step: dict[str, Any]) -> str:
    label = escape(current_step.get("label", "Current step"))
    detail = escape(current_step.get("detail", ""))
    status = current_step.get("status", "complete")
    status_text = "Running" if status == "active" else "Last step"
    detail_html = f'<p class="ci-h-current-detail">{detail}</p>' if detail else ""
    return (
        f'<div class="ci-h-current">'
        f'<div class="ci-h-current-top">'
        f'<span class="ci-h-current-label">{status_text}</span>'
        f'<span class="ci-h-current-step">{label}</span>'
        f"</div>"
        f"{detail_html}"
        f"</div>"
    )


def build_horizontal_pipeline_markup(
    phases: list[dict[str, str]],
    *,
    running: bool = False,
    current_step: dict[str, Any] | None = None,
) -> str:
    """Build compact HTML snapshot (used in tests)."""
    fill = _progress_percent(phases)
    phases_html = "".join(_phase_markup(phase) for phase in phases)
    running_html = (
        '<p class="ci-pipeline-running">'
        '<span class="ci-pipeline-running-dot"></span> Pipeline in progress</p>'
        if running
        else ""
    )
    current_html = _current_step_markup(current_step) if current_step else ""
    return (
        f'<div class="ci-pipeline-panel">'
        f'<div class="ci-pipeline-header">'
        f'<p class="ci-pipeline-title">Analysis Pipeline</p>{running_html}'
        f"</div>"
        f"{_progress_bar_markup(fill)}"
        f'<div class="ci-h-phases">{phases_html}</div>'
        f"{current_html}"
        f"</div>"
    )


def render_horizontal_pipeline(
    steps: list[dict[str, Any]] | None,
    *,
    running: bool = False,
) -> None:
    """Render grouped pipeline phases horizontally with active-step detail."""
    if not steps:
        return

    phases = compute_grouped_phase_status(steps)
    current = get_current_step(steps)
    fill = _progress_percent(phases)

    with st.container(border=True):
        header_l, header_r = st.columns([1, 1])
        with header_l:
            st.markdown(
                '<p class="ci-pipeline-title">Analysis Pipeline</p>',
                unsafe_allow_html=True,
            )
        with header_r:
            if running:
                st.markdown(
                    '<p class="ci-pipeline-running">'
                    '<span class="ci-pipeline-running-dot"></span> Pipeline in progress</p>',
                    unsafe_allow_html=True,
                )

        st.markdown(_progress_bar_markup(fill), unsafe_allow_html=True)

        cols = st.columns(5, gap="medium")
        for col, phase in zip(cols, phases):
            with col:
                st.markdown(_phase_markup(phase), unsafe_allow_html=True)

        if current:
            st.markdown(_current_step_markup(current), unsafe_allow_html=True)
