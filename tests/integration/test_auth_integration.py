"""Integration tests for authentication flow."""

import os
import tempfile
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.user import User, UserRole
from app.services.auth import MockAuthService


class TestAuthIntegration:
    """Integration tests for authentication components."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()

        db_url = f"sqlite:///{temp_file.name}"
        engine = create_engine(db_url)

        # Create tables
        SQLModel.metadata.create_all(engine)

        yield engine, db_url

        # Cleanup
        os.unlink(temp_file.name)

    def test_full_authentication_flow(self, temp_db):
        """Test complete authentication flow from token to user."""
        engine, db_url = temp_db

        # Mock get_engine to use our test database
        with patch('app.services.auth.get_engine', return_value=engine):
            # Test admin user creation
            admin_claims = {
                'sub': 'admin_google_sub',
                'email': 'admin@example.com',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }

            admin_auth_service = MockAuthService(admin_claims)

            # Mock admin emails setting
            with patch.object(admin_auth_service.settings, 'admin_emails', 'admin@example.com'):
                admin_user = admin_auth_service.authenticate_user("mock_token")

                assert admin_user.email == 'admin@example.com'
                assert admin_user.role == UserRole.ADMIN
                assert admin_user.is_active is True
                assert admin_user.google_sub == 'admin_google_sub'

    def test_user_persistence(self, temp_db):
        """Test that users are properly persisted and retrieved."""
        engine, db_url = temp_db

        with patch('app.services.auth.get_engine', return_value=engine):
            # Create first user
            student_claims = {
                'sub': 'student_google_sub',
                'email': 'student@example.com',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }

            auth_service = MockAuthService(student_claims)

            # First authentication - creates user
            user1 = auth_service.authenticate_user("mock_token")
            user1_id = user1.id

            # Second authentication - retrieves existing user
            user2 = auth_service.authenticate_user("mock_token")

            assert user1.id == user2.id
            assert user1.google_sub == user2.google_sub
            assert user1.email == user2.email

            # Verify user exists in database
            with Session(engine) as session:
                from sqlmodel import select
                statement = select(User).where(User.id == user1_id)
                db_user = session.exec(statement).first()

                assert db_user is not None
                assert db_user.email == 'student@example.com'
                assert db_user.role == UserRole.STUDENT

    def test_email_update_on_login(self, temp_db):
        """Test that user email is updated on subsequent logins."""
        engine, db_url = temp_db

        with patch('app.services.auth.get_engine', return_value=engine):
            # Create user with initial email
            initial_claims = {
                'sub': 'user_google_sub',
                'email': 'old@example.com',
                'email_verified': True,
                'iss': 'accounts.google.com'
            }

            auth_service = MockAuthService(initial_claims)
            user1 = auth_service.authenticate_user("mock_token")

            assert user1.email == 'old@example.com'

            # Login again with updated email
            updated_claims = {
                'sub': 'user_google_sub',  # Same Google sub
                'email': 'new@example.com',  # Updated email
                'email_verified': True,
                'iss': 'accounts.google.com'
            }

            auth_service_updated = MockAuthService(updated_claims)
            user2 = auth_service_updated.authenticate_user("mock_token")

            # Should be same user with updated email
            assert user1.id == user2.id
            assert user2.email == 'new@example.com'

    def test_multiple_users_different_roles(self, temp_db):
        """Test multiple users with different roles."""
        engine, db_url = temp_db

        with patch('app.services.auth.get_engine', return_value=engine):
            # Create admin user
            admin_service = MockAuthService({
                'sub': 'admin_sub',
                'email': 'admin@example.com',
                'email_verified': True,
                'iss': 'accounts.google.com'
            })

            # Create student user
            student_service = MockAuthService({
                'sub': 'student_sub',
                'email': 'student@example.com',
                'email_verified': True,
                'iss': 'accounts.google.com'
            })

            with patch.object(admin_service.settings, 'admin_emails', 'admin@example.com'):
                admin_user = admin_service.authenticate_user("token")

            with patch.object(student_service.settings, 'admin_emails', 'admin@example.com'):
                student_user = student_service.authenticate_user("token")

            # Verify different roles
            assert admin_user.role == UserRole.ADMIN
            assert student_user.role == UserRole.STUDENT

            # Verify both users exist in database
            with Session(engine) as session:
                from sqlmodel import select

                admin_query = select(User).where(User.google_sub == 'admin_sub')
                db_admin = session.exec(admin_query).first()

                student_query = select(User).where(User.google_sub == 'student_sub')
                db_student = session.exec(student_query).first()

                assert db_admin.role == UserRole.ADMIN
                assert db_student.role == UserRole.STUDENT
