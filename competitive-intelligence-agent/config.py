"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent
PLACEHOLDER_MARKERS = ("your_", "changeme", "replace_me", "xxx")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    tavily_api_key: str = ""

    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2

    database_path: str = "memory/competitive_intelligence.db"

    max_search_results: int = 5
    max_research_iterations: int = 3
    min_sources_per_major_claim: int = 2

    # RAG settings (Checkpoint 3.1)
    chroma_db_dir: str = "memory/chroma_db"
    rag_chunk_tokens: int = 650
    rag_chunk_overlap: float = 0.15
    rag_top_k: int = 6
    use_rag: bool = True

    # ToT settings (Checkpoint 4.1)
    tot_beam_width: int = 3
    tot_max_depth: int = 4
    tot_prune_threshold: int = 65

    # Safety settings (Checkpoint 6.1)
    escalation_confidence_threshold: float = 0.70
    require_human_approval: bool = True

    use_mcp: bool = True
    mcp_transport: str = "inprocess"  # inprocess | stdio

    def _is_real_secret(self, value: str) -> bool:
        if not value or not value.strip():
            return False
        lowered = value.strip().lower()
        return not any(marker in lowered for marker in PLACEHOLDER_MARKERS)

    @property
    def has_openai_api_key(self) -> bool:
        return self._is_real_secret(self.openai_api_key)

    @property
    def has_tavily_api_key(self) -> bool:
        return self._is_real_secret(self.tavily_api_key)

    @property
    def db_path(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_db_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


settings = Settings()
