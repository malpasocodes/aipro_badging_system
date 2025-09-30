"""Configuration management for the AIPPRO Badging System."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "AIPPRO Badging System"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # Logging
    log_level: str = "INFO"

    # Future: Database settings (Phase 4-5)
    # database_url: str = ""

    # Future: OAuth settings (Phase 2)
    # google_client_id: str = ""
    # google_client_secret: str = ""

    # Future: Security settings (Phase 2)
    # app_secret_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
