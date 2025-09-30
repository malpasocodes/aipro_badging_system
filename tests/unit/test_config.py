"""Unit tests for configuration management."""

from app.core.config import Settings, get_settings


class TestSettings:
    """Test configuration settings."""

    def test_default_settings(self) -> None:
        """Test default configuration values."""
        settings = Settings()

        assert settings.app_name == "AIPPRO Badging System"
        assert settings.app_version == "0.1.0"
        assert settings.app_env == "development"
        assert settings.debug is True
        assert settings.log_level == "INFO"

    def test_get_settings_returns_cached_instance(self) -> None:
        """Test that get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_with_custom_values(self) -> None:
        """Test settings with custom environment values."""
        settings = Settings(app_env="production", debug=False, log_level="ERROR")

        assert settings.app_env == "production"
        assert settings.debug is False
        assert settings.log_level == "ERROR"
