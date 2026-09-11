"""Tests for multi-provider LLM configuration."""

from unittest.mock import MagicMock, patch

import config
from agents.llm import LLMConfig, PROVIDER_DEFAULT_MODELS, get_active_llm_config, llm_context, validate_llm_ready


def test_ollama_validate_fails_when_server_down(monkeypatch):
    monkeypatch.setattr(
        "agents.llm.check_ollama_running",
        lambda base_url=None: (False, "Ollama is not running"),
    )
    cfg = LLMConfig(provider="ollama", model="llama3.2")
    ready, msg = validate_llm_ready(cfg)
    assert ready is False
    assert "Ollama" in msg


def test_ollama_validate_passes_when_server_up(monkeypatch):
    monkeypatch.setattr("agents.llm.check_ollama_running", lambda base_url=None: (True, ""))
    cfg = LLMConfig(provider="ollama", model="llama3.2")
    assert validate_llm_ready(cfg) == (True, "")


def test_groq_requires_api_key(monkeypatch):
    monkeypatch.setattr(config.settings, "groq_api_key", "")
    cfg = LLMConfig(provider="groq", model="llama-3.1-8b-instant")
    ready, msg = validate_llm_ready(cfg)
    assert ready is False
    assert "GROQ_API_KEY" in msg


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.setattr(config.settings, "openai_api_key", "")
    cfg = LLMConfig(provider="openai", model="gpt-4o-mini")
    ready, msg = validate_llm_ready(cfg)
    assert ready is False
    assert "OPENAI_API_KEY" in msg


def test_default_model_from_per_provider_settings(monkeypatch):
    monkeypatch.setattr(config.settings, "llm_provider", "ollama")
    monkeypatch.setattr(config.settings, "llm_model", "")
    monkeypatch.setattr(config.settings, "ollama_model", "mistral")
    cfg = LLMConfig.from_settings()
    assert cfg.model == "mistral"


def test_llm_context_overrides_active_config():
    default = get_active_llm_config()
    override = LLMConfig(provider="openai", model="gpt-4o-mini")
    with llm_context(override):
        assert get_active_llm_config().provider == "openai"
    assert get_active_llm_config().provider == default.provider


def test_from_inputs_uses_provider_specific_model(monkeypatch):
    monkeypatch.setattr(config.settings, "openai_model", "gpt-4o")
    cfg = LLMConfig.from_inputs(provider="openai", model="")
    assert cfg.model == "gpt-4o"


def test_fallback_to_provider_defaults():
    cfg = LLMConfig.from_inputs(provider="google", model="")
    assert cfg.model == PROVIDER_DEFAULT_MODELS["google"]


def test_llm_budget_limits_google_calls(monkeypatch):
    monkeypatch.setattr(config.settings, "google_max_llm_calls_per_run", 2)
    monkeypatch.setattr(config.settings, "cloud_llm_efficiency_mode", True)
    cfg = LLMConfig(provider="google", model="gemini-3.6-flash")

    with llm_context(cfg):
        from agents.llm import (
            can_invoke_llm,
            get_llm_call_count,
            invoke_llm,
            llm_budget_remaining,
        )

        assert llm_budget_remaining() == 2
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="ok")
        invoke_llm(mock_llm, [])
        invoke_llm(mock_llm, [])
        assert get_llm_call_count() == 2
        assert can_invoke_llm() is False
        assert llm_budget_remaining() == 0


def test_cloud_efficiency_mode_enabled_for_google(monkeypatch):
    monkeypatch.setattr(config.settings, "cloud_llm_efficiency_mode", True)
    monkeypatch.setattr(config.settings, "ollama_fast_mode", False)
    from agents.llm import is_cloud_efficiency_mode

    assert is_cloud_efficiency_mode("google") is True
    assert is_cloud_efficiency_mode("ollama") is False


def test_ollama_fast_mode_enabled_by_default(monkeypatch):
    monkeypatch.setattr(config.settings, "ollama_fast_mode", True)
    from agents.llm import is_cloud_efficiency_mode

    assert is_cloud_efficiency_mode("ollama") is True


def test_fast_mode_ui_override_disables_efficiency(monkeypatch):
    monkeypatch.setattr(config.settings, "ollama_fast_mode", True)
    cfg = LLMConfig(provider="ollama", model="llama3.2", fast_mode=False)
    with llm_context(cfg):
        from agents.llm import is_cloud_efficiency_mode

        assert is_cloud_efficiency_mode() is False


def test_fast_mode_ui_override_enables_openai(monkeypatch):
    monkeypatch.setattr(config.settings, "cloud_llm_efficiency_mode", False)
    cfg = LLMConfig(provider="openai", model="gpt-4o-mini", fast_mode=True)
    with llm_context(cfg):
        from agents.llm import is_cloud_efficiency_mode

        assert is_cloud_efficiency_mode() is True


def test_default_fast_mode_for_provider():
    from agents.llm import default_fast_mode_for_provider

    assert default_fast_mode_for_provider("ollama") == config.settings.ollama_fast_mode
