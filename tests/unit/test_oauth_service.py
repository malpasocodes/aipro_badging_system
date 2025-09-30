"""Unit tests for OAuth synchronization service."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.oauth import OAuthSyncService, OAuth2MockService, get_oauth_service
from app.models.user import User, UserRole


class TestOAuthSyncService:
    """Test cases for OAuthSyncService."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.oauth_service = OAuthSyncService()
    
    def test_sync_user_from_oauth_valid_data(self):
        """Test syncing user with valid OAuth data."""
        oauth_data = {
            'sub': 'google_sub_12345',
            'email': 'test@example.com',
            'name': 'Test User',
            'email_verified': True,
            'iss': 'accounts.google.com'
        }
        
        with patch.object(self.oauth_service.auth_service, 'get_or_create_user') as mock_get_create:
            mock_user = User(
                id="test-id",
                google_sub="google_sub_12345", 
                email="test@example.com",
                role=UserRole.STUDENT
            )
            mock_get_create.return_value = mock_user
            
            with patch('app.services.oauth.get_engine') as mock_get_engine:
                mock_session = MagicMock()
                mock_session.exec.return_value.first.return_value = mock_user
                mock_get_engine.return_value.__enter__.return_value = mock_session
                mock_get_engine.return_value.__exit__.return_value = None
                
                with patch('app.services.oauth.Session') as mock_session_class:
                    mock_session_class.return_value.__enter__.return_value = mock_session
                    mock_session_class.return_value.__exit__.return_value = None
                    
                    result = self.oauth_service.sync_user_from_oauth(oauth_data)
                    
                    assert result == mock_user
                    mock_get_create.assert_called_once_with("google_sub_12345", "test@example.com")
    
    def test_sync_user_from_oauth_missing_required_fields(self):
        """Test syncing user with missing required OAuth data."""
        # Missing 'sub' field
        oauth_data = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        with pytest.raises(ValueError, match="Missing required OAuth field: sub"):
            self.oauth_service.sync_user_from_oauth(oauth_data)
        
        # Missing 'email' field
        oauth_data = {
            'sub': 'google_sub_12345',
            'name': 'Test User'
        }
        
        with pytest.raises(ValueError, match="Missing required OAuth field: email"):
            self.oauth_service.sync_user_from_oauth(oauth_data)
    
    def test_sync_user_from_oauth_with_name_update(self):
        """Test syncing user with name update."""
        oauth_data = {
            'sub': 'google_sub_12345',
            'email': 'test@example.com',
            'name': 'Updated Name',
            'email_verified': True
        }
        
        with patch.object(self.oauth_service.auth_service, 'get_or_create_user') as mock_get_create:
            mock_user = User(
                id="test-id",
                google_sub="google_sub_12345",
                email="test@example.com", 
                role=UserRole.STUDENT,
                username=None  # No previous name
            )
            mock_get_create.return_value = mock_user
            
            with patch('app.services.oauth.get_engine') as mock_get_engine:
                mock_session = MagicMock()
                mock_session.exec.return_value.first.return_value = mock_user
                mock_get_engine.return_value.__enter__.return_value = mock_session
                mock_get_engine.return_value.__exit__.return_value = None
                
                with patch('app.services.oauth.Session') as mock_session_class:
                    mock_session_class.return_value.__enter__.return_value = mock_session
                    mock_session_class.return_value.__exit__.return_value = None
                    
                    result = self.oauth_service.sync_user_from_oauth(oauth_data)
                    
                    # Verify name was updated
                    assert mock_user.username == "Updated Name"
                    mock_session.add.assert_called()
                    mock_session.commit.assert_called()
    
    @patch('app.services.oauth.st')
    def test_get_current_user_authenticated(self, mock_st):
        """Test getting current user when authenticated."""
        # Mock st.user
        mock_st.user.is_logged_in = True
        
        mock_user_dict = {
            'sub': 'google_sub_123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        with patch('builtins.dict', return_value=mock_user_dict):
            with patch.object(self.oauth_service, 'sync_user_from_oauth') as mock_sync:
                mock_user = User(
                    id="test-id",
                    google_sub="google_sub_123",
                    email="test@example.com",
                    role=UserRole.STUDENT
                )
                mock_sync.return_value = mock_user
                
                result = self.oauth_service.get_current_user()
                
                assert result == mock_user
                mock_sync.assert_called_once_with(mock_user_dict)
    
    @patch('app.services.oauth.st')
    def test_get_current_user_not_authenticated(self, mock_st):
        """Test getting current user when not authenticated."""
        mock_st.user.is_logged_in = False
        
        result = self.oauth_service.get_current_user()
        
        assert result is None
    
    @patch('app.services.oauth.st')
    def test_is_authenticated_true(self, mock_st):
        """Test is_authenticated when user is logged in."""
        mock_st.user.is_logged_in = True
        
        result = self.oauth_service.is_authenticated()
        
        assert result is True
    
    @patch('app.services.oauth.st')
    def test_is_authenticated_false(self, mock_st):
        """Test is_authenticated when user is not logged in."""
        mock_st.user.is_logged_in = False
        
        result = self.oauth_service.is_authenticated()
        
        assert result is False
    
    @patch('app.services.oauth.st')
    def test_get_oauth_user_info_authenticated(self, mock_st):
        """Test getting OAuth user info when authenticated."""
        mock_st.user.is_logged_in = True
        
        # Mock the dict() conversion of st.user
        mock_user_dict = {
            'sub': 'google_sub_123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        with patch('builtins.dict', return_value=mock_user_dict):
            result = self.oauth_service.get_oauth_user_info()
            
            expected = {
                'sub': 'google_sub_123',
                'email': 'test@example.com', 
                'name': 'Test User'
            }
            assert result == expected
    
    @patch('app.services.oauth.st')
    def test_get_oauth_user_info_not_authenticated(self, mock_st):
        """Test getting OAuth user info when not authenticated."""
        mock_st.user.is_logged_in = False
        
        result = self.oauth_service.get_oauth_user_info()
        
        assert result is None


class TestOAuth2MockService:
    """Test cases for OAuth2MockService."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_service = OAuth2MockService()
    
    def test_mock_login_default_data(self):
        """Test mock login with default user data."""
        with patch.object(self.mock_service, 'sync_user_from_oauth') as mock_sync:
            mock_user = User(
                id="test-id",
                google_sub="mock_oauth_sub_123",
                email="oauth-test@example.com",
                role=UserRole.STUDENT
            )
            mock_sync.return_value = mock_user
            
            result = self.mock_service.mock_login()
            
            assert result == mock_user
            assert self.mock_service.is_logged_in is True
            mock_sync.assert_called_once_with(self.mock_service.mock_user_data)
    
    def test_mock_login_custom_data(self):
        """Test mock login with custom user data."""
        custom_data = {
            'sub': 'custom_sub_456',
            'email': 'custom@example.com',
            'name': 'Custom User'
        }
        
        with patch.object(self.mock_service, 'sync_user_from_oauth') as mock_sync:
            mock_user = User(
                id="test-id",
                google_sub="custom_sub_456",
                email="custom@example.com",
                role=UserRole.ADMIN
            )
            mock_sync.return_value = mock_user
            
            result = self.mock_service.mock_login(custom_data)
            
            assert result == mock_user
            mock_sync.assert_called_once_with(custom_data)
    
    def test_mock_logout(self):
        """Test mock logout functionality."""
        # First login
        self.mock_service.is_logged_in = True
        
        # Then logout
        self.mock_service.mock_logout()
        
        assert self.mock_service.is_logged_in is False
    
    def test_is_authenticated_mock(self):
        """Test mock authentication status."""
        # Not authenticated initially
        assert self.mock_service.is_authenticated() is False
        
        # Login
        self.mock_service.is_logged_in = True
        assert self.mock_service.is_authenticated() is True
        
        # Logout
        self.mock_service.is_logged_in = False
        assert self.mock_service.is_authenticated() is False
    
    def test_get_current_user_mock_authenticated(self):
        """Test getting current user from mock when authenticated."""
        self.mock_service.is_logged_in = True
        
        with patch.object(self.mock_service, 'sync_user_from_oauth') as mock_sync:
            mock_user = User(
                id="test-id",
                google_sub="mock_oauth_sub_123",
                email="oauth-test@example.com",
                role=UserRole.STUDENT
            )
            mock_sync.return_value = mock_user
            
            result = self.mock_service.get_current_user()
            
            assert result == mock_user
    
    def test_get_current_user_mock_not_authenticated(self):
        """Test getting current user from mock when not authenticated."""
        self.mock_service.is_logged_in = False
        
        result = self.mock_service.get_current_user()
        
        assert result is None
    
    def test_get_oauth_user_info_mock_authenticated(self):
        """Test getting OAuth user info from mock when authenticated."""
        self.mock_service.is_logged_in = True
        
        result = self.mock_service.get_oauth_user_info()
        
        assert result == self.mock_service.mock_user_data
    
    def test_get_oauth_user_info_mock_not_authenticated(self):
        """Test getting OAuth user info from mock when not authenticated."""
        self.mock_service.is_logged_in = False
        
        result = self.mock_service.get_oauth_user_info()
        
        assert result is None


class TestGetOAuthService:
    """Test cases for get_oauth_service factory function."""
    
    @patch('app.services.oauth.get_settings')
    def test_get_oauth_service_production(self, mock_get_settings):
        """Test getting OAuth service in production mode."""
        mock_settings = MagicMock()
        mock_settings.debug = False
        mock_get_settings.return_value = mock_settings
        
        result = get_oauth_service()
        
        assert isinstance(result, OAuthSyncService)
        assert not isinstance(result, OAuth2MockService)
    
    @patch('app.services.oauth.get_settings')
    def test_get_oauth_service_development_mock_disabled(self, mock_get_settings):
        """Test getting OAuth service in development with mock disabled."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.enable_mock_auth = False
        mock_get_settings.return_value = mock_settings
        
        result = get_oauth_service()
        
        assert isinstance(result, OAuthSyncService)
        assert not isinstance(result, OAuth2MockService)
    
    @patch('app.services.oauth.get_settings')
    def test_get_oauth_service_development_mock_enabled(self, mock_get_settings):
        """Test getting OAuth service in development with mock enabled."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.enable_mock_auth = True
        mock_get_settings.return_value = mock_settings
        
        result = get_oauth_service()
        
        assert isinstance(result, OAuth2MockService)