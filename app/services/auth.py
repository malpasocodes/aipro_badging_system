"""Authentication service for Google ID token verification and user management."""

from datetime import datetime
from typing import Any

from google.auth.transport import requests
from google.oauth2 import id_token
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.user import User, UserRole

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Authentication-related errors."""
    pass


class AuthService:
    """Authentication service for Google ID token verification."""

    def __init__(self):
        self.settings = get_settings()

    def verify_google_id_token(self, id_token_str: str) -> dict[str, Any]:
        """
        Verify Google ID token and return user claims.
        
        Args:
            id_token_str: The ID token from Google
            
        Returns:
            Dictionary with user claims (sub, email, name, etc.)
            
        Raises:
            AuthenticationError: If token verification fails
        """
        try:
            # Verify the token
            request = requests.Request()
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                request,
                self.settings.google_client_id
            )

            # Verify issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise AuthenticationError("Invalid token issuer")

            # Verify email is verified
            if not id_info.get('email_verified', False):
                raise AuthenticationError("Email not verified")

            logger.info("ID token verified successfully", email=id_info.get('email'))
            return id_info

        except ValueError as e:
            logger.error("ID token verification failed", error=str(e))
            raise AuthenticationError("Invalid ID token") from e
        except Exception as e:
            logger.error("Unexpected error during token verification", error=str(e))
            raise AuthenticationError("Token verification failed") from e

    def get_or_create_user(self, google_sub: str, email: str) -> User:
        """
        Get existing user or create new user from Google OAuth data.

        Args:
            google_sub: Google's unique user identifier
            email: User's email address

        Returns:
            User object
        """
        engine = get_engine()

        with Session(engine) as session:
            # First try to find existing user by google_sub
            statement = select(User).where(User.google_sub == google_sub)
            user = session.exec(statement).first()

            if user:
                # Update last login and email (in case it changed)
                user.email = email
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()

                # Check if role should be updated based on current admin list
                expected_role = self._determine_user_role(email)
                if user.role != expected_role:
                    logger.info(
                        "Updating user role based on admin list",
                        user_id=str(user.id),
                        email=email,
                        old_role=user.role.value,
                        new_role=expected_role.value
                    )
                    user.role = expected_role

                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info("Existing user logged in (by google_sub)", user_id=str(user.id), email=email)
                return user

            # If not found by google_sub, try by email (for mock OAuth compatibility)
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if user:
                # User exists with this email but different google_sub
                # Update google_sub (allows mock OAuth to work with real OAuth users)
                logger.warning(
                    "User found by email with different google_sub - updating",
                    user_id=str(user.id),
                    email=email,
                    old_google_sub=user.google_sub,
                    new_google_sub=google_sub
                )
                user.google_sub = google_sub
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()

                # Check if role should be updated based on current admin list
                expected_role = self._determine_user_role(email)
                if user.role != expected_role:
                    logger.info(
                        "Updating user role based on admin list",
                        user_id=str(user.id),
                        email=email,
                        old_role=user.role.value,
                        new_role=expected_role.value
                    )
                    user.role = expected_role

                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info("Existing user logged in (by email)", user_id=str(user.id), email=email)
                return user

            # Create new user (no existing user found)
            role = self._determine_user_role(email)
            user = User(
                google_sub=google_sub,
                email=email,
                role=role,
                last_login_at=datetime.utcnow()
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            logger.info("New user created", user_id=str(user.id), email=email, role=role.value)
            return user

    def _determine_user_role(self, email: str) -> UserRole:
        """
        Determine user role based on email and admin list.
        
        Args:
            email: User's email address
            
        Returns:
            UserRole enum value
        """
        admin_emails = self.settings.admin_emails

        if admin_emails:
            admin_list = [email.strip().lower() for email in admin_emails.split(',')]
            if email.lower() in admin_list:
                return UserRole.ADMIN

        # Default to student role
        return UserRole.STUDENT

    def authenticate_user(self, id_token_str: str) -> User:
        """
        Authenticate user with Google ID token.
        
        Args:
            id_token_str: The ID token from Google
            
        Returns:
            Authenticated User object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Verify the ID token
        claims = self.verify_google_id_token(id_token_str)

        # Extract user information
        google_sub = claims['sub']
        email = claims['email']

        # Get or create user
        user = self.get_or_create_user(google_sub, email)

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    def get_user_by_id(self, user_id: str) -> User | None:
        """
        Get user by ID.
        
        Args:
            user_id: User's UUID as string
            
        Returns:
            User object or None if not found
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).first()


# Mock verifier for testing
class MockAuthService(AuthService):
    """Mock authentication service for testing."""

    def __init__(self, mock_claims: dict[str, Any] | None = None):
        super().__init__()
        self.mock_claims = mock_claims or {
            'sub': 'mock_google_sub_123',
            'email': 'test@example.com',
            'email_verified': True,
            'iss': 'accounts.google.com'
        }

    def verify_google_id_token(self, id_token_str: str) -> dict[str, Any]:
        """Mock ID token verification."""
        if id_token_str == "invalid_token":
            raise AuthenticationError("Invalid ID token")

        return self.mock_claims
