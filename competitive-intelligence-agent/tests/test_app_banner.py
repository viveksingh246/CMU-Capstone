"""Tests for sticky app banner markup."""

from agents.llm import LLMConfig
from ui.components import build_app_banner_markup


def test_build_app_banner_markup_includes_title_and_banner_class():
    markup = build_app_banner_markup(LLMConfig.from_inputs(provider="ollama", model="llama3.2"))
    assert "ci-sticky-banner" in markup
    assert "Competitive Intelligence Research Agent" in markup
    assert "ci-sticky-badges" in markup
    assert "ci-logo-svg" in markup
