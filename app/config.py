"""Central configuration for the Lost & Found Agent.

All runtime settings are read from environment variables (or a local `.env`
file) exactly once, here, and exposed as a single typed `settings` object.
The rest of the app imports `from app.config import settings` instead of
touching `os.environ` directly — so there is one place to see, validate, and
override configuration.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, loaded from the environment / `.env`.

    Field names map to the UPPER_CASE variables documented in `.env.example`
    (pydantic-settings matches them case-insensitively).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- PostgreSQL + pgvector ----
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lostfound"

    # ---- LLM (Ollama, OpenAI-compatible endpoint) ----
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"  # placeholder; Ollama ignores it
    llm_model: str = "llama3.1:latest"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 512

    # ---- Embeddings (local sentence-transformers) ----
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ---- Retrieval / RAG ----
    retrieval_top_k: int = 5

    # ---- Confidence / guardrail thresholds ----
    confidence_high_threshold: float = 0.75
    confidence_low_threshold: float = 0.45

    # ---- MCP server ----
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8765

    # ---- API server ----
    api_host: str = "127.0.0.1"
    api_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


# Convenient module-level singleton for `from app.config import settings`.
settings = get_settings()
