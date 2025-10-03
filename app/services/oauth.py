"""OAuth integration service for Streamlit native authentication."""

from datetime import datetime
from typing import Any

import streamlit as st
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.user import User
from app.services.auth import AuthService

logger = get_logger(__name__)


def _is_streamlit_user_authenticated() -> bool:
    """Best-effort check for Streamlit native auth status across versions."""
    if not hasattr(st, "user"):
        return False

    user_proxy = st.user

    # Prefer explicit boolean flags exposed by Streamlit
    for attr in ("is_logged_in", "is_authenticated", "logged_in", "authenticated"):
        value = getattr(user_proxy, attr, None)
        if value is not None:
            return bool(value)

    # Fall back to presence of core identity fields
    try:
        user_dict = dict(user_proxy)
    except Exception:
        return False

    return bool(user_dict.get("email") or user_dict.get("sub"))


class OAuthSyncService:
    """Synchronize st.user OAuth data with application user database."""

    def __init__(self):
        self.settings = get_settings()
        self.auth_service = AuthService()

    def sync_user_from_oauth(self, oauth_user_data: dict[str, Any]) -> User:
        """
        Create or update user from st.user OAuth data.
        
        Args:
            oauth_user_data: Dictionary containing OAuth user data from st.user
            
        Returns:
            User object synchronized with database
            
        Raises:
            ValueError: If required OAuth data is missing
        """
        # Validate required OAuth data
        required_fields = ['email', 'sub']
        for field in required_fields:
            if field not in oauth_user_data:
                raise ValueError(f"Missing required OAuth field: {field}")

        google_sub = oauth_user_data['sub']
        email = oauth_user_data['email']

        # Use existing auth service logic for user creation/update
        user = self.auth_service.get_or_create_user(google_sub, email)

        # Update any additional OAuth fields if available
        engine = get_engine()
        with Session(engine) as session:
            # Refresh user object and update additional fields
            statement = select(User).where(User.id == user.id)
            db_user = session.exec(statement).first()

            if db_user:
                # Track if we need to update
                needs_update = False

                # Update name if available in OAuth data
                if 'name' in oauth_user_data and oauth_user_data['name']:
                    if db_user.username != oauth_user_data['name']:
                        db_user.username = oauth_user_data['name']
                        needs_update = True

                # Always update login timestamp
                db_user.last_login_at = datetime.utcnow()
                db_user.updated_at = datetime.utcnow()
                needs_update = True

                if needs_update:
                    session.add(db_user)
                    session.commit()
                    session.refresh(db_user)

                logger.info(
                    "OAuth user synchronized",
                    user_id=str(db_user.id),
                    email=email,
                    role=db_user.role.value,
                    name=db_user.username
                )
                return db_user

        return user

    def get_current_user(self) -> User | None:
        """
        Get current user from st.user with database synchronization.
        
        Returns:
            User object if authenticated and synced, None otherwise
        """
        # Check if user is authenticated via Streamlit native auth
        if not _is_streamlit_user_authenticated():
            return None

        try:
            # Convert st.user to dictionary for processing
            oauth_data = dict(st.user)

            # Sync with database and return user
            return self.sync_user_from_oauth(oauth_data)

        except Exception as e:
            logger.error("Failed to sync OAuth user", error=str(e))
            return None

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated via st.user.
        
        Returns:
            True if user is authenticated, False otherwise
        """
        return _is_streamlit_user_authenticated()

    def get_oauth_user_info(self) -> dict[str, Any] | None:
        """
        Get raw OAuth user information from st.user.
        
        Returns:
            Dictionary with OAuth user data, None if not authenticated
        """
        if not self.is_authenticated():
            return None

        return dict(st.user)

    def sign_out(self) -> None:
        """
        Sign out the current user using Streamlit's native logout.
        """
        if hasattr(st, 'logout'):
            st.logout()
        else:
            logger.warning("st.logout not available - user may need to clear browser session")


class OAuth2MockService(OAuthSyncService):
    """Mock OAuth service for testing and development."""

    def __init__(self, mock_user_data: dict[str, Any] | None = None):
        super().__init__()
        self.mock_user_data = mock_user_data or {
            'sub': 'mock_oauth_sub_123',
            'email': 'oauth-test@example.com',
            'name': 'OAuth Test User',
            'email_verified': True,
            'iss': 'accounts.google.com'
        }
        self.is_logged_in = False

    def mock_login(self, user_data: dict[str, Any] | None = None) -> User:
        """
        Simulate OAuth login for testing.
        
        Args:
            user_data: Optional user data to use for mock login
            
        Returns:
            User object created from mock data
        """
        data = user_data or self.mock_user_data
        self.is_logged_in = True
        return self.sync_user_from_oauth(data)

    def mock_logout(self) -> None:
        """Simulate OAuth logout for testing."""
        self.is_logged_in = False

    def is_authenticated(self) -> bool:
        """Check mock authentication status."""
        return self.is_logged_in

    def get_current_user(self) -> User | None:
        """Get current user from mock OAuth data."""
        if not self.is_authenticated():
            return None

        return self.sync_user_from_oauth(self.mock_user_data)

    def get_oauth_user_info(self) -> dict[str, Any] | None:
        """Get mock OAuth user information."""
        if not self.is_authenticated():
            return None

        return self.mock_user_data.copy()


def get_oauth_service() -> OAuthSyncService:
    """
    Get appropriate OAuth service based on configuration.
    
    Returns:
        OAuthSyncService or OAuth2MockService based on settings
    """
    settings = get_settings()

    # Use mock service in development if enabled
    if settings.debug and getattr(settings, 'enable_mock_auth', False):
        return OAuth2MockService()

    return OAuthSyncService()
