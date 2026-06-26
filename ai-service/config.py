"""Environment-driven settings (pydantic-settings). Reads .env + real env vars."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # AI service
    ai_service_api_key: str = "change-me-local-dev-key"
    log_level: str = "info"
    allowed_origins: str = "http://localhost:8080"

    # Database (Postgres + pgvector)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_platform"

    # Gemini (hosted inference)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "text-embedding-004"
    embedding_dim: int = 768

    # Provider selection (alternate inference backend)
    inference_provider: str = "gemini"  # gemini | vllm
    vllm_base_url: str = ""
    vllm_model: str = ""

    # Retrieval
    retrieval_top_k: int = 5

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
