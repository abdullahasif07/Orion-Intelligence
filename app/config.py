"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Orion.

    Values are loaded from environment variables and an optional `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="Default OpenAI model")

    # Tool API keys
    newsapi_key: str = Field(default="", description="NewsAPI.org key")
    openweathermap_api_key: str = Field(default="", description="OpenWeatherMap key")
    brave_search_api_key: str = Field(default="", description="Brave Search API key")

    # Agent loop
    max_agent_iterations: int = Field(default=5, ge=1, le=20)
    tool_timeout_seconds: float = Field(default=15.0, gt=0)
    tool_cache_ttl_seconds: float = Field(default=60.0, ge=0)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
