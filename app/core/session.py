"""Session management utilities for Streamlit authentication state."""

from datetime import datetime, timedelta

import streamlit as st

from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

# Session timeout in minutes (Phase 2B will make this configurable)
SESSION_TIMEOUT_MINUTES = 60


class SessionManager:
    """Manages user session state and authentication."""

    @staticmethod
    def start_session(user: User) -> None:
        """Start a new user session."""
        st.session_state.user = user
        st.session_state.authenticated = True
        st.session_state.login_time = datetime.utcnow()
        st.session_state.last_activity = datetime.utcnow()

        logger.info("Session started", user_id=str(user.id), email=user.email)

    @staticmethod
    def end_session() -> None:
        """End the current user session."""
        user_id = None
        email = None

        if 'user' in st.session_state:
            user = st.session_state.user
            user_id = str(user.id)
            email = user.email

        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        logger.info("Session ended", user_id=user_id, email=email)

    @staticmethod
    def get_current_user() -> User | None:
        """Get the currently authenticated user."""
        if not st.session_state.get("authenticated", False):
            return None

        # Check session timeout
        if SessionManager._is_session_expired():
            logger.info("Session expired, logging out user")
            SessionManager.end_session()
            return None

        # Update last activity
        st.session_state.last_activity = datetime.utcnow()

        return st.session_state.get("user")

    @staticmethod
    def _is_session_expired() -> bool:
        """Check if the current session has expired."""
        last_activity = st.session_state.get("last_activity")

        if not last_activity:
            return True

        timeout_delta = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return datetime.utcnow() - last_activity > timeout_delta

    @staticmethod
    def get_session_info() -> dict:
        """Get information about the current session."""
        if not st.session_state.get("authenticated", False):
            return {"authenticated": False}

        login_time = st.session_state.get("login_time")
        last_activity = st.session_state.get("last_activity")

        session_duration = None
        time_since_activity = None

        if login_time:
            session_duration = datetime.utcnow() - login_time

        if last_activity:
            time_since_activity = datetime.utcnow() - last_activity

        return {
            "authenticated": True,
            "login_time": login_time,
            "last_activity": last_activity,
            "session_duration": session_duration,
            "time_since_activity": time_since_activity,
            "expires_in": timedelta(minutes=SESSION_TIMEOUT_MINUTES) - time_since_activity if time_since_activity else None
        }

    @staticmethod
    def is_admin() -> bool:
        """Check if the current user is an admin."""
        user = SessionManager.get_current_user()
        return user is not None and user.role.value == "ADMIN"

    @staticmethod
    def require_role(required_role: str) -> User:
        """Require a specific user role."""
        user = SessionManager.get_current_user()

        if not user:
            st.error("🔐 Authentication required")
            st.stop()

        if user.role.value != required_role:
            st.error(f"🚫 Access denied. {required_role} role required.")
            st.stop()

        return user
