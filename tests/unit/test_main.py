"""Unit tests for main application entry point."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.user import UserRole


class _StubStreamlit:
    """Simple stub for streamlit module to isolate side effects."""

    def __init__(self):
        self.set_page_config = MagicMock()
        self.title = MagicMock()
        self.markdown = MagicMock()
        self.warning = MagicMock()
        self.success = MagicMock()
        self.info = MagicMock()
        self.write = MagicMock()
        self.query_params = {}
        self.__version__ = "1.50.0"
        self.session_state = {}
        self.errors = MagicMock(StreamlitAuthError=Exception)

    def __getattr__(self, name):
        if name == "dialog":
            def decorator(*_args, **_kwargs):
                def wrapper(func):
                    return func

                return wrapper

            return decorator

        mock = MagicMock()
        setattr(self, name, mock)
        return mock


stub_streamlit = _StubStreamlit()
sys.modules['streamlit'] = stub_streamlit
sys.modules['streamlit.errors'] = SimpleNamespace(StreamlitAuthError=Exception)

from app.main import main


class TestMain:
    """Test cases for main application entry point."""

    @patch("app.main.setup_logging")
    @patch("app.main.get_settings")
    @patch("app.main.render_admin_dashboard")
    @patch("app.main.render_user_info")
    @patch("app.main.require_authentication")
    @patch("app.main.is_oauth_available", return_value=False)
    @patch("app.main.get_current_user")
    def test_main_with_authenticated_user(
        self,
        mock_get_current_user,
        _mock_is_oauth_available,
        mock_require_authentication,
        mock_render_user_info,
        mock_render_admin_dashboard,
        mock_get_settings,
        mock_setup_logging,
    ) -> None:
        """Test main function when a user is already authenticated."""
        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_user.username = "Admin"
        mock_user.is_onboarded.return_value = True
        mock_get_current_user.return_value = mock_user

        mock_settings = type("Settings", (), {"debug": False})()
        mock_get_settings.return_value = mock_settings

        main()

        mock_setup_logging.assert_called_once()
        stub_streamlit.set_page_config.assert_called_once()
        mock_render_user_info.assert_called_once_with(mock_user)
        mock_render_admin_dashboard.assert_called_once_with(mock_user)
        mock_require_authentication.assert_not_called()

    @patch("app.main.render_onboarding_form")
    @patch("app.main.get_settings")
    @patch("app.main.render_user_info")
    @patch("app.main.require_authentication")
    @patch("app.main.is_oauth_available", return_value=False)
    @patch("app.main.get_current_user")
    def test_main_with_non_onboarded_user(
        self,
        mock_get_current_user,
        _mock_is_oauth_available,
        mock_require_authentication,
        mock_render_user_info,
        mock_get_settings,
        mock_render_onboarding_form,
    ) -> None:
        """Test main function when user is authenticated but not onboarded."""
        mock_user = MagicMock()
        mock_user.is_onboarded.return_value = False
        mock_get_current_user.return_value = mock_user

        mock_settings = type("Settings", (), {"debug": False})()
        mock_get_settings.return_value = mock_settings

        main()

        mock_render_onboarding_form.assert_called_once()
        mock_render_user_info.assert_not_called()
        mock_require_authentication.assert_not_called()

    @patch("app.main.require_oauth_authentication")
    @patch("app.main.get_current_oauth_user", return_value=None)
    @patch("app.main.is_oauth_available", return_value=True)
    def test_main_without_authenticated_user(
        self,
        _mock_is_oauth_available,
        mock_get_current_oauth_user,
        mock_require_oauth_authentication,
    ) -> None:
        """Test main function when no user is authenticated."""
        with patch("app.main.st", stub_streamlit):
            main()

        mock_require_oauth_authentication.assert_called_once()
        mock_get_current_oauth_user.assert_called_once()
