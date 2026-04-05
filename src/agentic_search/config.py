from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (folder with pyproject.toml), so .env loads even if cwd is elsewhere
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    search_provider: str = Field(default="brave", description="brave | serpapi | fixture")

    brave_api_key: str = ""
    serpapi_key: str = ""

    # Prefer OPENROUTER_API_KEY for OpenRouter; otherwise use OpenAI-compatible key + URL.
    openrouter_api_key: str = ""
    openrouter_http_referer: str = ""
    openrouter_x_title: str = "AgenticSearch"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    top_k_urls: int = 8
    max_chars_per_page: int = 12_000
    fetch_timeout_s: float = 20.0
    llm_timeout_s: float = 120.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


_DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def uses_openrouter(settings: Settings) -> bool:
    return bool(settings.openrouter_api_key.strip())


def effective_llm_key(settings: Settings) -> str:
    if settings.openrouter_api_key.strip():
        return settings.openrouter_api_key.strip()
    return settings.openai_api_key.strip()


def effective_llm_base_url(settings: Settings) -> str:
    """OpenRouter base URL when OPENROUTER_API_KEY is set, unless OPENAI_BASE_URL overrides."""
    base = (settings.openai_base_url or "").strip()
    if settings.openrouter_api_key.strip():
        if not base or base == _DEFAULT_OPENAI_BASE:
            return _OPENROUTER_BASE
        return base
    return base if base else _DEFAULT_OPENAI_BASE
