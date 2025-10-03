"""Authentication UI components for Google Sign-in."""


import streamlit as st

from app.core.logging import get_logger
from app.core.session import SessionManager
from app.models.user import User
from app.services.auth import AuthenticationError, MockAuthService

logger = get_logger(__name__)


def render_google_signin() -> None:
    """Render Google Sign-in button and handle authentication."""
    st.markdown("### 🔐 Sign In")
    st.markdown("Please sign in with your Google account to access the badging system.")

    # For Phase 2A, we'll use a simple form to simulate Google sign-in
    # In Phase 2B, this will be replaced with actual Google OAuth
    with st.form("google_signin_form"):
        st.markdown("**Demo Authentication** (Phase 2A)")
        st.info("Enter any valid email to simulate Google sign-in. Admin emails from .env will have admin role.")

        email = st.text_input(
            "Email Address",
            placeholder="user@example.com",
            help="Use admin@example.com for admin access"
        )

        use_mock = st.checkbox(
            "Use Mock Authentication",
            value=True,
            help="Uses mock authentication service for testing"
        )

        submitted = st.form_submit_button("Sign In with Google", type="primary")

        if submitted and email:
            try:
                # Use mock authentication for Phase 2A
                if use_mock:
                    auth_service = MockAuthService({
                        'sub': f'mock_google_sub_{hash(email)}',
                        'email': email,
                        'email_verified': True,
                        'iss': 'accounts.google.com'
                    })
                    # Simulate ID token
                    user = auth_service.authenticate_user("mock_valid_token")
                else:
                    # This would be real Google authentication in Phase 2B
                    st.error("Real Google authentication not yet implemented. Please use mock authentication.")
                    return

                # Start user session
                SessionManager.start_session(user)

                logger.info("User authenticated successfully", user_id=str(user.id), email=user.email)
                st.success(f"Welcome, {user.email}! You are signed in as {user.role.value.lower()}.")
                st.rerun()

            except AuthenticationError as e:
                logger.error("Authentication failed", error=str(e), email=email)
                st.error(f"Authentication failed: {str(e)}")
            except Exception as e:
                logger.error("Unexpected authentication error", error=str(e), email=email)
                st.error("An unexpected error occurred during sign-in. Please try again.")


def render_user_info(user: User) -> None:
    """Render user information and sign-out option."""
    with st.sidebar:
        st.markdown("### 👤 User Information")
        st.write(f"**Email:** {user.email}")
        st.write(f"**Role:** {user.role.value}")
        st.write(f"**Status:** {'Active' if user.is_active else 'Inactive'}")

        if user.last_login_at:
            st.write(f"**Last Login:** {user.last_login_at.strftime('%Y-%m-%d %H:%M')}")

        # Show session information
        session_info = SessionManager.get_session_info()
        if session_info.get("session_duration"):
            duration = session_info["session_duration"]
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            st.write(f"**Session:** {int(hours)}h {int(minutes)}m")

        st.markdown("---")

        if st.button("Sign Out", type="secondary"):
            SessionManager.end_session()
            st.success("You have been signed out.")
            st.rerun()


def get_current_user() -> User | None:
    """Get the currently authenticated user from session state."""
    return SessionManager.get_current_user()


def require_authentication() -> User | None:
    """Require authentication and return current user or show sign-in form."""
    user = get_current_user()

    if user is None:
        render_google_signin()
        st.stop()

    return user


def require_admin() -> User:
    """Require admin authentication and return current user."""
    return SessionManager.require_role("ADMIN")
