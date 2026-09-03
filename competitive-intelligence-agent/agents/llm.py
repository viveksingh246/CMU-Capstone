"""Shared LLM utilities."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from config import settings


def get_llm() -> BaseChatModel:
    if not settings.has_openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your API key."
        )
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key,
    )


def load_prompt(name: str) -> str:
    from pathlib import Path

    prompts_dir = Path(__file__).parent.parent / "prompts"
    for candidate in (f"{name}.txt", f"{name}_prompt.txt"):
        prompt_path = prompts_dir / candidate
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt not found: {name}")
