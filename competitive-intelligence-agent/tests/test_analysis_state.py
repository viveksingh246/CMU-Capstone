"""Tests for analysis workflow button state helpers."""

from ui.analysis_state import (
    can_approve_result,
    can_export_result,
    can_run_analysis,
    is_pending_human_review,
    request_approve_finalize,
    request_run_analysis,
)


def test_can_run_analysis_false_when_pipeline_running():
    class Session:
        def get(self, key, default=None):
            if key == "pipeline_running":
                return True
            return default

    import ui.analysis_state as state

    original = state.st.session_state
    state.st.session_state = Session()
    try:
        assert can_run_analysis() is False
    finally:
        state.st.session_state = original


def test_can_approve_only_when_review_required():
    assert can_approve_result({"requires_human_review": True}) is True
    assert can_approve_result({"requires_human_review": False}) is False
    assert (
        can_approve_result({"requires_human_review": True, "human_approved": True}) is False
    )


def test_can_approve_false_when_pipeline_running():
    class Session(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import ui.analysis_state as state

    original = state.st.session_state
    state.st.session_state = Session(pipeline_running=True)
    try:
        assert can_approve_result({"requires_human_review": True}) is False
    finally:
        state.st.session_state = original


def test_can_export_when_complete_not_pending_review():
    result = {
        "requires_human_review": False,
        "final_report": "# Brief",
        "findings": [{"claim": "x"}],
    }
    assert can_export_result(result) is True
    assert can_export_result({**result, "requires_human_review": True}) is False


def test_can_export_after_human_approval_even_if_escalation_flag_remains():
    result = {
        "requires_human_review": True,
        "human_approved": True,
        "final_report": "# Brief",
        "findings": [{"claim": "x"}],
    }
    assert can_export_result(result) is True


def test_request_run_sets_pending_flags():
    class Session(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import ui.analysis_state as state

    original = state.st.session_state
    state.st.session_state = Session()
    try:
        request_run_analysis()
        assert state.st.session_state["analysis_run_pending"] is True
        assert state.st.session_state.get("pipeline_running") is not True
    finally:
        state.st.session_state = original


def test_request_approve_sets_pending_when_review_required():
    class Session(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import ui.analysis_state as state

    original = state.st.session_state
    state.st.session_state = Session(last_result={"requires_human_review": True})
    try:
        request_approve_finalize()
        assert state.st.session_state["approve_finalize_pending"] is True
        assert state.st.session_state["pipeline_running"] is True
    finally:
        state.st.session_state = original


def test_request_approve_ignored_when_pipeline_running():
    class Session(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import ui.analysis_state as state

    original = state.st.session_state
    state.st.session_state = Session(
        pipeline_running=True,
        last_result={"requires_human_review": True},
    )
    try:
        request_approve_finalize()
        assert "approve_finalize_pending" not in state.st.session_state
    finally:
        state.st.session_state = original
