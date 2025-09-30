"""Unit tests for main application."""

from unittest.mock import patch

from app.main import main


class TestMain:
    """Test main application functionality."""

    @patch("app.main.setup_logging")
    @patch("app.main.get_settings")
    @patch("streamlit.set_page_config")
    @patch("streamlit.title")
    @patch("streamlit.write")
    @patch("streamlit.info")
    def test_main_function_calls_expected_functions(
        self,
        mock_info,
        mock_write,
        mock_title,
        mock_set_page_config,
        mock_get_settings,
        mock_setup_logging,
    ) -> None:
        """Test that main function calls expected setup functions."""
        # Mock settings
        mock_settings = type("Settings", (), {})()
        mock_get_settings.return_value = mock_settings

        # Call main function
        main()

        # Verify setup functions were called
        mock_setup_logging.assert_called_once()
        mock_get_settings.assert_called_once()
        mock_set_page_config.assert_called_once()

        # Verify Streamlit UI functions were called
        mock_title.assert_called_once_with("🏆 AIPPRO Badging System")
        mock_write.assert_called_once_with(
            "Welcome to the AIPPRO Digital Badging System"
        )
        mock_info.assert_called_once()

    def test_main_function_exists(self) -> None:
        """Test that main function exists and is callable."""
        assert callable(main)
