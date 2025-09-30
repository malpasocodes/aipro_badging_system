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

    # Database settings (Phase 2A)
    database_url: str = ""

    # Authentication settings (Phase 2A)
    google_client_id: str = ""
    admin_emails: str = ""  # Comma-separated list of admin emails

    # Development Settings
    streamlit_server_headless: str = "false"
    streamlit_server_port: str = "8501"

    # Future: Security settings (Phase 2B)
    # app_secret_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
