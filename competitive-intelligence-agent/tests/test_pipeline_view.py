"""Tests for horizontal pipeline progress UI."""

from ui.pipeline_view import (
    build_horizontal_pipeline_markup,
    get_current_step,
    _progress_percent,
)


def test_get_current_step_prefers_active():
    steps = [
        {"label": "First", "status": "complete"},
        {"label": "Second", "status": "active", "detail": "working"},
    ]
    current = get_current_step(steps)
    assert current is not None
    assert current["label"] == "Second"


def test_progress_percent_marks_active_phase_midpoint():
    phases = [
        {"status": "complete"},
        {"status": "complete"},
        {"status": "active"},
        {"status": "pending"},
        {"status": "pending"},
    ]
    assert _progress_percent(phases) == 62.5


def test_build_horizontal_pipeline_markup_includes_active_class():
    phases = [
        {"num": "1", "title": "Intake", "status": "complete"},
        {"num": "2", "title": "Research", "status": "active"},
        {"num": "3", "title": "Extract", "status": "pending"},
        {"num": "4", "title": "Analyze", "status": "pending"},
        {"num": "5", "title": "Deliver", "status": "pending"},
    ]
    markup = build_horizontal_pipeline_markup(
        phases,
        running=True,
        current_step={"label": "Search sources", "detail": "3 documents", "status": "active"},
    )
    assert "ci-h-phase-active" in markup
    assert "ci-pipeline-running-dot" in markup
    assert "Search sources" in markup
    assert "ci-h-progress-bar" in markup
