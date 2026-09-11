"""Shared LLM utilities with multi-provider support."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from config import settings

PROVIDER_DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "groq": "llama-3.1-8b-instant",
    "google": "gemini-3.6-flash",
    "openai": "gpt-4o-mini",
}

PROVIDER_INFO = {
    "ollama": {
        "label": "Ollama (Free, Local)",
        "tier": "free",
        "hint": "Install from ollama.com, then: ollama pull llama3.2",
    },
    "groq": {
        "label": "Groq (Free Cloud)",
        "tier": "free",
        "hint": "Set GROQ_API_KEY in .env — console.groq.com",
    },
    "google": {
        "label": "Google Gemini (Free Cloud)",
        "tier": "free",
        "hint": "Set GOOGLE_API_KEY in .env — aistudio.google.com/apikey",
    },
    "openai": {
        "label": "OpenAI (Paid)",
        "tier": "paid",
        "hint": "Set OPENAI_API_KEY in .env",
    },
}

_active_llm_config: ContextVar[LLMConfig | None] = ContextVar("active_llm_config", default=None)
_llm_call_count: ContextVar[int] = ContextVar("llm_call_count", default=0)


class LLMBudgetExhausted(Exception):
    """Raised when a workflow exceeds the configured per-run LLM call budget."""


def reset_llm_budget() -> None:
    _llm_call_count.set(0)


def get_llm_call_count() -> int:
    return _llm_call_count.get()


def get_max_llm_calls_for_provider(provider: str) -> int | None:
    """Return per-run call cap, or None for unlimited (Ollama / paid OpenAI)."""
    if settings.max_llm_calls_per_run > 0:
        return settings.max_llm_calls_per_run
    normalized = provider.lower()
    if normalized == "google":
        return settings.google_max_llm_calls_per_run
    if normalized == "groq":
        return settings.groq_max_llm_calls_per_run
    return None


def default_fast_mode_for_provider(provider: str) -> bool:
    """Env-based default for whether Fast Mode is on for a provider."""
    normalized = provider.lower()
    if normalized == "ollama":
        return settings.ollama_fast_mode
    if not settings.cloud_llm_efficiency_mode:
        return False
    return normalized in {"google", "groq", "openai"}


def resolve_fast_mode(config: LLMConfig | None = None) -> bool:
    """Effective Fast Mode for the active or supplied LLM config."""
    cfg = config or get_active_llm_config()
    if cfg.fast_mode is not None:
        return cfg.fast_mode
    return default_fast_mode_for_provider(cfg.provider)


def is_cloud_efficiency_mode(provider: str | None = None) -> bool:
    """Reduce LLM/search work per run (cloud quotas or local Ollama speed)."""
    cfg = get_active_llm_config()
    resolved = (provider or cfg.provider).lower()
    if cfg.fast_mode is not None:
        return cfg.fast_mode
    if resolved == "ollama":
        return settings.ollama_fast_mode
    if not settings.cloud_llm_efficiency_mode:
        return False
    return resolved in {"google", "groq", "openai"}


def get_effective_max_research_iterations() -> int:
    if is_cloud_efficiency_mode():
        return settings.fast_mode_max_research_iterations
    return settings.max_research_iterations


def get_effective_max_queries_per_pass() -> int:
    if is_cloud_efficiency_mode():
        return settings.fast_mode_max_queries_per_pass
    return 5


def llm_budget_remaining(provider: str | None = None) -> int | None:
    max_calls = get_max_llm_calls_for_provider(provider or get_active_llm_config().provider)
    if max_calls is None:
        return None
    return max(0, max_calls - get_llm_call_count())


def can_invoke_llm(provider: str | None = None) -> bool:
    remaining = llm_budget_remaining(provider)
    return remaining is None or remaining > 0


def invoke_llm(llm: BaseChatModel, messages: list[BaseMessage]) -> Any:
    """Invoke the LLM and enforce per-run call budget for quota-limited providers."""
    cfg = get_active_llm_config()
    if not can_invoke_llm(cfg.provider):
        raise LLMBudgetExhausted(
            f"LLM call budget exhausted for {cfg.provider} "
            f"(limit: {get_max_llm_calls_for_provider(cfg.provider)} calls/run). "
            "Wait for quota reset, switch to Ollama, or raise the limit in .env."
        )
    _llm_call_count.set(get_llm_call_count() + 1)
    return llm.invoke(messages)


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float = 0.2
    fast_mode: bool | None = None

    @classmethod
    def from_settings(cls) -> LLMConfig:
        provider = settings.llm_provider.lower()
        return cls(
            provider=provider,
            model=_resolve_model(provider, settings.llm_model),
            temperature=settings.llm_temperature,
            fast_mode=None,
        )

    @classmethod
    def from_inputs(
        cls,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        fast_mode: bool | None = None,
    ) -> LLMConfig:
        resolved_provider = (provider or settings.llm_provider).lower()
        resolved_model = _resolve_model(
            resolved_provider,
            model if model is not None else settings.get_model_for_provider(resolved_provider),
        )
        return cls(
            provider=resolved_provider,
            model=resolved_model,
            temperature=temperature if temperature is not None else settings.llm_temperature,
            fast_mode=fast_mode,
        )


def _resolve_model(provider: str, model: str | None) -> str:
    cleaned = (model or "").strip()
    if cleaned and not (cleaned == "gpt-4o-mini" and provider != "openai"):
        return cleaned
    env_model = settings.get_model_for_provider(provider)
    if env_model:
        return env_model
    return PROVIDER_DEFAULT_MODELS.get(provider, cleaned or "llama3.2")


def get_active_llm_config() -> LLMConfig:
    override = _active_llm_config.get()
    if override is not None:
        return override
    return LLMConfig.from_settings()


@contextmanager
def llm_context(config: LLMConfig | None) -> Iterator[LLMConfig]:
    """Apply a runtime LLM config for the duration of a workflow run."""
    active = config or LLMConfig.from_settings()
    token = _active_llm_config.set(active)
    reset_llm_budget()
    try:
        yield active
    finally:
        _active_llm_config.reset(token)


def has_llm_available(config: LLMConfig | None = None) -> bool:
    """Return whether credentials exist for the given provider."""
    cfg = config or get_active_llm_config()
    provider = cfg.provider.lower()
    if provider == "ollama":
        return True
    if provider == "groq":
        return settings.has_groq_api_key
    if provider == "google":
        return settings.has_google_api_key
    if provider == "openai":
        return settings.has_openai_api_key
    return False


def check_ollama_running(base_url: str | None = None) -> tuple[bool, str]:
    """Verify the local Ollama server is reachable."""
    url = (base_url or settings.ollama_base_url).rstrip("/")
    try:
        import httpx

        response = httpx.get(f"{url}/api/tags", timeout=3.0)
        if response.status_code == 200:
            return True, ""
        return False, f"Ollama server returned HTTP {response.status_code}"
    except Exception as exc:
        error = str(exc).lower()
        if "connection refused" in error or "connect" in error:
            return False, (
                "Ollama is not running. Fix options:\n"
                "1. Install Ollama from https://ollama.com\n"
                "2. Start it: `ollama serve` (or open the Ollama app)\n"
                "3. Pull a model: `ollama pull llama3.2`\n"
                "— OR switch provider in the sidebar to Groq / Google / OpenAI"
            )
        return False, f"Cannot reach Ollama at {url}: {exc}"


def validate_llm_ready(config: LLMConfig | None = None) -> tuple[bool, str]:
    """Pre-flight check before starting analysis."""
    cfg = config or get_active_llm_config()
    provider = cfg.provider.lower()

    if provider == "groq" and not settings.has_groq_api_key:
        return False, "Set GROQ_API_KEY in .env (free at console.groq.com)"
    if provider == "google" and not settings.has_google_api_key:
        return False, "Set GOOGLE_API_KEY in .env (free at aistudio.google.com/apikey)"
    if provider == "openai" and not settings.has_openai_api_key:
        return False, "Set OPENAI_API_KEY in .env"
    if provider == "ollama":
        return check_ollama_running()

    return True, ""


def provider_status(config: LLMConfig | None = None) -> dict[str, str]:
    """Human-readable readiness status for UI badges."""
    cfg = config or get_active_llm_config()
    ready, message = validate_llm_ready(cfg)
    tier = PROVIDER_INFO.get(cfg.provider, {}).get("tier", "unknown")
    return {
        "provider": cfg.provider,
        "model": cfg.model,
        "tier": tier,
        "ready": ready,
        "message": message,
        "label": PROVIDER_INFO.get(cfg.provider, {}).get("label", cfg.provider),
    }


def get_effective_model(config: LLMConfig | None = None) -> str:
    return (config or get_active_llm_config()).model


def get_llm(config: LLMConfig | None = None) -> BaseChatModel:
    cfg = config or get_active_llm_config()
    provider = cfg.provider.lower()
    model = cfg.model
    temperature = cfg.temperature

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise ValueError(
                "Ollama provider requires langchain-ollama. Run: pip install langchain-ollama"
            ) from exc
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=settings.ollama_base_url,
        )

    if provider == "groq":
        if not settings.has_groq_api_key:
            raise ValueError("GROQ_API_KEY is not set. Get a free key at https://console.groq.com")
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise ValueError("Groq provider requires langchain-groq.") from exc
        return ChatGroq(model=model, temperature=temperature, api_key=settings.groq_api_key)

    if provider == "google":
        if not settings.has_google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
            )
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ValueError("Google provider requires langchain-google-genai.") from exc
        return ChatGoogleGenerativeAI(
            model=model, temperature=temperature, google_api_key=settings.google_api_key
        )

    if provider == "openai":
        if not settings.has_openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, temperature=temperature, api_key=settings.openai_api_key)

    raise ValueError(
        f"Unknown LLM provider '{cfg.provider}'. Use: ollama, groq, google, or openai"
    )


def load_prompt(name: str) -> str:
    from pathlib import Path

    prompts_dir = Path(__file__).parent.parent / "prompts"
    for candidate in (f"{name}.txt", f"{name}_prompt.txt"):
        prompt_path = prompts_dir / candidate
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt not found: {name}")
