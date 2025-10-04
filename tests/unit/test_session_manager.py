"""Unit tests for session management."""

# Mock streamlit before importing SessionManager
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from unittest.mock import MagicMock, patch


class SessionStateProxy(dict):
    """Simple proxy that supports attribute access like Streamlit session state."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key, value):
        self[key] = value


class _StubStreamlit:
    def __init__(self):
        self.session_state = SessionStateProxy()
        self.error = MagicMock()
        self.stop = MagicMock()


mock_streamlit = _StubStreamlit()
sys.modules['streamlit'] = mock_streamlit

from app.core.session import SessionManager
from app.models.user import User, UserRole


class TestSessionManager:
    """Test cases for SessionManager."""

    def setup_method(self):
        """Set up test dependencies."""
        # Mock streamlit session_state
        self.mock_session_state = {}

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_start_session(self, mock_st_session_state):
        """Test starting a new session."""
        user = User(
            id="test-id",
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT
        )

        SessionManager.start_session(user)

        assert mock_st_session_state['user'] == user
        assert mock_st_session_state['authenticated'] is True
        assert 'login_time' in mock_st_session_state
        assert 'last_activity' in mock_st_session_state

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_end_session(self, mock_st_session_state):
        """Test ending a session."""
        # Set up session state
        mock_st_session_state['user'] = MagicMock()
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['login_time'] = datetime.utcnow()

        SessionManager.end_session()

        assert len(mock_st_session_state) == 0

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_get_current_user_valid_session(self, mock_st_session_state):
        """Test getting current user with valid session."""
        user = User(
            id="test-id",
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT
        )

        # Set up valid session
        mock_st_session_state['user'] = user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = datetime.utcnow()

        result = SessionManager.get_current_user()

        assert result == user
        # Should update last_activity
        assert 'last_activity' in mock_st_session_state

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_get_current_user_expired_session(self, mock_st_session_state):
        """Test getting current user with expired session."""
        user = User(
            id="test-id",
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT
        )

        # Set up expired session (2 hours ago)
        expired_time = datetime.utcnow() - timedelta(hours=2)
        mock_st_session_state['user'] = user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = expired_time

        result = SessionManager.get_current_user()

        assert result is None
        # Session should be cleared
        assert len(mock_st_session_state) == 0

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_get_current_user_no_session(self, mock_st_session_state):
        """Test getting current user with no session."""
        result = SessionManager.get_current_user()
        assert result is None

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_get_session_info_authenticated(self, mock_st_session_state):
        """Test getting session info for authenticated user."""
        login_time = datetime.utcnow() - timedelta(minutes=30)
        last_activity = datetime.utcnow() - timedelta(minutes=5)

        mock_st_session_state['authenticated'] = True
        mock_st_session_state['login_time'] = login_time
        mock_st_session_state['last_activity'] = last_activity

        info = SessionManager.get_session_info()

        assert info['authenticated'] is True
        assert info['login_time'] == login_time
        assert info['last_activity'] == last_activity
        assert info['session_duration'] is not None
        assert info['time_since_activity'] is not None
        assert info['expires_in'] is not None

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_get_session_info_not_authenticated(self, mock_st_session_state):
        """Test getting session info for non-authenticated user."""
        info = SessionManager.get_session_info()
        assert info == {"authenticated": False}

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_is_admin_true(self, mock_st_session_state):
        """Test is_admin with admin user."""
        admin_user = User(
            id="admin-id",
            google_sub="admin_sub",
            email="admin@example.com",
            role=UserRole.ADMIN
        )
        admin_user.role = SimpleNamespace(value="ADMIN")

        mock_st_session_state['user'] = admin_user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = datetime.utcnow()

        assert SessionManager.is_admin() is True

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_is_admin_false(self, mock_st_session_state):
        """Test is_admin with non-admin user."""
        student_user = User(
            id="student-id",
            google_sub="student_sub",
            email="student@example.com",
            role=UserRole.STUDENT
        )
        student_user.role = SimpleNamespace(value="STUDENT")
        student_user.role = SimpleNamespace(value="STUDENT")

        mock_st_session_state['user'] = student_user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = datetime.utcnow()

        assert SessionManager.is_admin() is False

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    def test_is_admin_no_user(self, mock_st_session_state):
        """Test is_admin with no user."""
        assert SessionManager.is_admin() is False

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    @patch('app.core.session.st.error')
    @patch('app.core.session.st.stop')
    def test_require_role_success(self, mock_stop, mock_error, mock_st_session_state):
        """Test require_role with correct role."""
        admin_user = User(
            id="admin-id",
            google_sub="admin_sub",
            email="admin@example.com",
            role=UserRole.ADMIN
        )
        admin_user.role = SimpleNamespace(value="ADMIN")

        mock_st_session_state['user'] = admin_user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = datetime.utcnow()

        result = SessionManager.require_role("ADMIN")

        assert result == admin_user
        mock_error.assert_not_called()
        mock_stop.assert_not_called()

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    @patch('app.core.session.st.error')
    @patch('app.core.session.st.stop')
    def test_require_role_wrong_role(self, mock_stop, mock_error, mock_st_session_state):
        """Test require_role with wrong role."""
        student_user = User(
            id="student-id",
            google_sub="student_sub",
            email="student@example.com",
            role=UserRole.STUDENT
        )
        student_user.role = SimpleNamespace(value="STUDENT")

        mock_st_session_state['user'] = student_user
        mock_st_session_state['authenticated'] = True
        mock_st_session_state['last_activity'] = datetime.utcnow()

        mock_stop.side_effect = RuntimeError("st.stop")

        with pytest.raises(RuntimeError):
            SessionManager.require_role("ADMIN")

        mock_error.assert_called_once()
        mock_stop.assert_called_once()

    @patch('app.core.session.st.session_state', new_callable=SessionStateProxy)
    @patch('app.core.session.st.error')
    @patch('app.core.session.st.stop')
    def test_require_role_no_user(self, mock_stop, mock_error, mock_st_session_state):
        """Test require_role with no authenticated user."""
        mock_stop.side_effect = RuntimeError("st.stop")

        with pytest.raises(RuntimeError):
            SessionManager.require_role("ADMIN")

        mock_error.assert_called_once()
        mock_stop.assert_called_once()
