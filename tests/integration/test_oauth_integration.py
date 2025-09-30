"""Integration tests for OAuth authentication flow."""

import pytest
from unittest.mock import patch
import tempfile
import os

from app.services.oauth import OAuthSyncService, OAuth2MockService
from app.models.user import User, UserRole
from app.core.database import get_engine
from sqlmodel import SQLModel, Session, create_engine


class TestOAuthIntegration:
    """Integration tests for OAuth authentication components."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database for testing."""
        # Use in-memory database for each test
        db_url = "sqlite:///:memory:"
        engine = create_engine(db_url)
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        
        yield engine, db_url
        
        # No cleanup needed for in-memory database
    
    def test_oauth_user_creation_flow(self, temp_db):
        """Test complete OAuth user creation and synchronization."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            oauth_service = OAuthSyncService()
            
            # Mock OAuth data from Google
            oauth_data = {
                'sub': 'google_oauth_sub_123',
                'email': 'oauth-user@example.com',
                'name': 'OAuth User',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            # Test user creation
            with patch.object(oauth_service.settings, 'admin_emails', 'admin@example.com'):
                user = oauth_service.sync_user_from_oauth(oauth_data)
                
                assert user.email == 'oauth-user@example.com'
                assert user.google_sub == 'google_oauth_sub_123'
                assert user.username == 'OAuth User'
                assert user.role == UserRole.STUDENT
                assert user.is_active is True
    
    def test_oauth_admin_user_creation(self, temp_db):
        """Test OAuth admin user creation via ADMIN_EMAILS."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            oauth_service = OAuthSyncService()
            
            # Admin OAuth data
            oauth_data = {
                'sub': 'google_admin_sub_456',
                'email': 'admin@example.com',
                'name': 'Admin User',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            # Test admin user creation
            with patch.object(oauth_service.settings, 'admin_emails', 'admin@example.com,other@example.com'):
                user = oauth_service.sync_user_from_oauth(oauth_data)
                
                assert user.email == 'admin@example.com'
                assert user.role == UserRole.ADMIN
                assert user.username == 'Admin User'
    
    def test_oauth_user_update_flow(self, temp_db):
        """Test OAuth user update on subsequent logins."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            oauth_service = OAuthSyncService()
            
            # Initial OAuth data
            initial_data = {
                'sub': 'google_user_sub_789',
                'email': 'user@example.com',
                'name': 'Initial Name',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            # Create initial user
            with patch.object(oauth_service.settings, 'admin_emails', 'admin@example.com'):
                user1 = oauth_service.sync_user_from_oauth(initial_data)
                user1_id = user1.id
                
                # Updated OAuth data (name changed)
                updated_data = {
                    'sub': 'google_user_sub_789',  # Same sub
                    'email': 'user@example.com',   # Same email
                    'name': 'Updated Name',        # Different name
                    'email_verified': True,
                    'iss': 'accounts.google.com'
                }
                
                # Update user
                user2 = oauth_service.sync_user_from_oauth(updated_data)
                
                # Should be same user with updated info
                assert user1.id == user2.id
                assert user2.username == 'Updated Name'
                assert user2.email == 'user@example.com'
                assert user2.google_sub == 'google_user_sub_789'
    
    def test_oauth_email_update_flow(self, temp_db):
        """Test OAuth user email update (rare but possible)."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            oauth_service = OAuthSyncService()
            
            # Initial OAuth data
            initial_data = {
                'sub': 'google_user_sub_999',
                'email': 'old-email@example.com',
                'name': 'Test User',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            # Create initial user
            with patch.object(oauth_service.settings, 'admin_emails', 'admin@example.com'):
                user1 = oauth_service.sync_user_from_oauth(initial_data)
                
                # Updated OAuth data with new email (same Google sub)
                updated_data = {
                    'sub': 'google_user_sub_999',      # Same sub
                    'email': 'new-email@example.com',  # Different email
                    'name': 'Test User',
                    'email_verified': True,
                    'iss': 'accounts.google.com'
                }
                
                # Update user
                user2 = oauth_service.sync_user_from_oauth(updated_data)
                
                # Should be same user with updated email
                assert user1.id == user2.id
                assert user2.email == 'new-email@example.com'
                assert user2.google_sub == 'google_user_sub_999'
    
    def test_multiple_oauth_users_different_roles(self, temp_db):
        """Test multiple OAuth users with different roles."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            oauth_service = OAuthSyncService()
            
            # Admin user data
            admin_data = {
                'sub': 'google_admin_sub_multi',
                'email': 'multi-admin@example.com',
                'name': 'Multi Admin User',
                'email_verified': True
            }
            
            # Student user data
            student_data = {
                'sub': 'google_student_sub_multi',
                'email': 'multi-student@example.com', 
                'name': 'Multi Student User',
                'email_verified': True
            }
            
            with patch.object(oauth_service.settings, 'admin_emails', 'multi-admin@example.com'):
                # Create admin user
                admin_user = oauth_service.sync_user_from_oauth(admin_data)
                
                # Create student user
                student_user = oauth_service.sync_user_from_oauth(student_data)
                
                # Verify different roles
                assert admin_user.role == UserRole.ADMIN
                assert student_user.role == UserRole.STUDENT
                
                # Verify users exist in database
                with Session(engine) as session:
                    from sqlmodel import select
                    
                    admin_query = select(User).where(User.google_sub == 'google_admin_sub_multi')
                    db_admin = session.exec(admin_query).first()
                    
                    student_query = select(User).where(User.google_sub == 'google_student_sub_multi')
                    db_student = session.exec(student_query).first()
                    
                    assert db_admin.role == UserRole.ADMIN
                    assert db_student.role == UserRole.STUDENT
                    assert db_admin.username == 'Multi Admin User'
                    assert db_student.username == 'Multi Student User'


class TestOAuth2MockServiceIntegration:
    """Integration tests for mock OAuth service."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database for testing."""
        # Use in-memory database for each test
        db_url = "sqlite:///:memory:"
        engine = create_engine(db_url)
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        
        yield engine, db_url
        
        # No cleanup needed for in-memory database
    
    def test_mock_oauth_full_flow(self, temp_db):
        """Test complete mock OAuth flow with database integration."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            mock_service = OAuth2MockService()
            
            # Test login
            with patch.object(mock_service.settings, 'admin_emails', 'admin@example.com'):
                user = mock_service.mock_login()
                
                assert user.email == 'oauth-test@example.com'
                assert user.google_sub == 'mock_oauth_sub_123'
                assert user.username == 'OAuth Test User'
                assert user.role == UserRole.STUDENT
                assert mock_service.is_authenticated() is True
                
                # Test getting current user
                current_user = mock_service.get_current_user()
                assert current_user.id == user.id
                
                # Test OAuth info
                oauth_info = mock_service.get_oauth_user_info()
                assert oauth_info['email'] == 'oauth-test@example.com'
                assert oauth_info['sub'] == 'mock_oauth_sub_123'
                
                # Test logout
                mock_service.mock_logout()
                assert mock_service.is_authenticated() is False
                assert mock_service.get_current_user() is None
    
    def test_mock_oauth_custom_data_flow(self, temp_db):
        """Test mock OAuth with custom user data."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            custom_data = {
                'sub': 'custom_mock_sub_456',
                'email': 'custom@example.com',
                'name': 'Custom Mock User',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            mock_service = OAuth2MockService(custom_data)
            
            with patch.object(mock_service.settings, 'admin_emails', 'admin@example.com'):
                user = mock_service.mock_login()
                
                assert user.email == 'custom@example.com'
                assert user.google_sub == 'custom_mock_sub_456'
                assert user.username == 'Custom Mock User'
                assert user.role == UserRole.STUDENT
    
    def test_mock_oauth_admin_role_assignment(self, temp_db):
        """Test mock OAuth admin role assignment."""
        engine, db_url = temp_db
        
        with patch('app.services.oauth.get_engine', return_value=engine), \
             patch('app.services.auth.get_engine', return_value=engine):
            admin_data = {
                'sub': 'mock_admin_sub_unique_789',
                'email': 'mock-admin@example.com',
                'name': 'Mock Admin User',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }
            
            mock_service = OAuth2MockService(admin_data)
            
            with patch.object(mock_service.settings, 'admin_emails', 'mock-admin@example.com'):
                user = mock_service.mock_login()
                
                assert user.email == 'mock-admin@example.com'
                assert user.role == UserRole.ADMIN
                assert user.username == 'Mock Admin User'