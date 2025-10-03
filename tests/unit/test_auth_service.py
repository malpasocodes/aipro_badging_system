"""Unit tests for authentication service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User, UserRole
from app.services.auth import AuthenticationError, AuthService, MockAuthService


class TestAuthService:
    """Test cases for AuthService."""

    def setup_method(self):
        """Set up test dependencies."""
        self.auth_service = AuthService()

    def test_determine_user_role_admin(self):
        """Test admin role assignment from ADMIN_EMAILS."""
        with patch.object(self.auth_service.settings, 'admin_emails', 'admin@example.com,admin2@example.com'):
            role = self.auth_service._determine_user_role('admin@example.com')
            assert role == UserRole.ADMIN

    def test_determine_user_role_admin_case_insensitive(self):
        """Test admin role assignment is case insensitive."""
        with patch.object(self.auth_service.settings, 'admin_emails', 'admin@example.com'):
            role = self.auth_service._determine_user_role('ADMIN@EXAMPLE.COM')
            assert role == UserRole.ADMIN

    def test_determine_user_role_student_default(self):
        """Test default student role assignment."""
        with patch.object(self.auth_service.settings, 'admin_emails', 'admin@example.com'):
            role = self.auth_service._determine_user_role('student@example.com')
            assert role == UserRole.STUDENT

    def test_determine_user_role_empty_admin_list(self):
        """Test student role when admin_emails is empty."""
        with patch.object(self.auth_service.settings, 'admin_emails', ''):
            role = self.auth_service._determine_user_role('any@example.com')
            assert role == UserRole.STUDENT

    @patch('app.services.auth.get_engine')
    def test_get_or_create_user_existing(self, mock_get_engine):
        """Test retrieving existing user."""
        # Mock database session and user
        mock_session = MagicMock()
        mock_user = User(
            id="test-id",
            google_sub="existing_sub",
            email="existing@example.com",
            role=UserRole.STUDENT,
            last_login_at=datetime(2025, 1, 1)
        )

        mock_session.exec.return_value.first.return_value = mock_user
        mock_engine = MagicMock()
        mock_engine.__enter__ = MagicMock(return_value=mock_session)
        mock_engine.__exit__ = MagicMock(return_value=None)
        mock_get_engine.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_engine.return_value.__exit__ = MagicMock(return_value=None)

        with patch('app.services.auth.Session') as mock_session_class:
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session_class.return_value.__exit__.return_value = None

            user = self.auth_service.get_or_create_user("existing_sub", "updated@example.com")

            # Verify user email was updated
            assert mock_user.email == "updated@example.com"
            mock_session.add.assert_called()
            mock_session.commit.assert_called()

    @patch('app.services.auth.get_engine')
    def test_get_or_create_user_new(self, mock_get_engine):
        """Test creating new user."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None  # No existing user

        with patch('app.services.auth.Session') as mock_session_class:
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session_class.return_value.__exit__.return_value = None

            with patch.object(self.auth_service, '_determine_user_role', return_value=UserRole.STUDENT):
                user = self.auth_service.get_or_create_user("new_sub", "new@example.com")

                mock_session.add.assert_called()
                mock_session.commit.assert_called()


class TestMockAuthService:
    """Test cases for MockAuthService."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_auth_service = MockAuthService()

    def test_verify_google_id_token_valid(self):
        """Test valid token verification."""
        claims = self.mock_auth_service.verify_google_id_token("valid_token")

        assert claims['sub'] == 'mock_google_sub_123'
        assert claims['email'] == 'test@example.com'
        assert claims['email_verified'] is True
        assert claims['iss'] == 'accounts.google.com'

    def test_verify_google_id_token_invalid(self):
        """Test invalid token verification."""
        with pytest.raises(AuthenticationError, match="Invalid ID token"):
            self.mock_auth_service.verify_google_id_token("invalid_token")

    def test_custom_mock_claims(self):
        """Test MockAuthService with custom claims."""
        custom_claims = {
            'sub': 'custom_sub',
            'email': 'custom@example.com',
            'email_verified': True,
            'iss': 'accounts.google.com'
        }

        mock_service = MockAuthService(custom_claims)
        claims = mock_service.verify_google_id_token("any_token")

        assert claims == custom_claims

    @patch('app.services.auth.get_engine')
    def test_authenticate_user_success(self, mock_get_engine):
        """Test successful user authentication."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None  # New user

        with patch('app.services.auth.Session') as mock_session_class:
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session_class.return_value.__exit__.return_value = None

            with patch.object(self.mock_auth_service, '_determine_user_role', return_value=UserRole.STUDENT):
                user = self.mock_auth_service.authenticate_user("valid_token")

                assert user.email == 'test@example.com'
                assert user.google_sub == 'mock_google_sub_123'

    @patch('app.services.auth.get_engine')
    def test_authenticate_user_inactive(self, mock_get_engine):
        """Test authentication of inactive user."""
        mock_session = MagicMock()
        mock_user = User(
            id="test-id",
            google_sub="mock_google_sub_123",
            email="test@example.com",
            role=UserRole.STUDENT,
            is_active=False  # Inactive user
        )
        mock_session.exec.return_value.first.return_value = mock_user

        with patch('app.services.auth.Session') as mock_session_class:
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session_class.return_value.__exit__.return_value = None

            with pytest.raises(AuthenticationError, match="User account is inactive"):
                self.mock_auth_service.authenticate_user("valid_token")
