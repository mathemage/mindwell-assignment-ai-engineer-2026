"""Core configuration management."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://mindwell:mindwell_dev_password@localhost:5432/mindwell"
    )

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Security
    secret_key: str = Field(default="dev_secret_key_change_in_production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.7

    # Safety
    enable_crisis_detection: bool = True
    enable_pii_redaction: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # LLM Settings
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000
    llm_timeout: int = 30

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
