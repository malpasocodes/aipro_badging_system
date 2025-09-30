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

    # OAuth Configuration (Phase 2B)
    google_client_secret: str = ""
    auth_cookie_secret: str = ""
    auth_redirect_uri: str = "http://localhost:8501/oauth2callback"
    
    # Development toggles (Phase 2B)
    enable_mock_auth: bool = False  # For testing environments
    debug_auth: bool = False        # Show auth debugging info

    # Development Settings
    streamlit_server_headless: str = "false"
    streamlit_server_port: str = "8501"

    # Future: Security settings (Phase 2B+)
    # app_secret_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
