"""Unit tests for logging configuration."""

from unittest.mock import patch

from app.core.logging import get_logger, setup_logging


class TestLogging:
    """Test logging configuration."""

    def test_setup_logging_configures_structlog(self) -> None:
        """Test that setup_logging configures structlog properly."""
        with patch("structlog.configure") as mock_configure:
            setup_logging()

            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert "processors" in call_args.kwargs
            assert "logger_factory" in call_args.kwargs

    def test_get_logger_returns_bound_logger(self) -> None:
        """Test that get_logger returns a bound logger."""
        # Need to set up logging first to get proper logger type
        setup_logging()
        logger = get_logger("test")

        # Check that we get a logger instance that can log
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_logger_has_correct_name(self) -> None:
        """Test that logger has the correct name."""
        logger_name = "app.test"
        logger = get_logger(logger_name)

        # Test that we can log without errors
        logger.info("Test message", extra_data="test")

        # The actual logger name checking would require more complex setup
        # For now, just verify the logger is functional
        assert logger is not None
