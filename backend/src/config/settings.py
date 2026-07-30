"""
Application Configuration

Responsibility:
    Loads application configuration from environment variables.

Used by:
    Entire application.

Why:
    Avoid hardcoded values and keep configuration centralized.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    DEBUG: bool
    API_PREFIX: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    lru_cache ensures the configuration is loaded only once
    during the application's lifetime.
    """
    return Settings()
