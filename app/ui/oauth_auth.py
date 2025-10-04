"""OAuth authentication UI components using Streamlit native authentication."""


import streamlit as st
from streamlit.errors import StreamlitAuthError

from app.core.logging import get_logger
from app.core.secrets_bootstrap import ensure_streamlit_secrets_file
from app.models.user import User
from app.services.oauth import OAuth2MockService, get_oauth_service

REQUIRED_OAUTH_SECRETS = (
    "client_id",
    "client_secret",
    "cookie_secret",
    "redirect_uri",
    "server_metadata_url",
)

logger = get_logger(__name__)


def _get_missing_oauth_config_keys() -> list[str]:
    """Return required OAuth secret keys that are missing or empty."""
    ensure_streamlit_secrets_file()
    if not hasattr(st, "secrets"):
        return list(REQUIRED_OAUTH_SECRETS)

    try:
        auth_section = st.secrets["auth"]
    except KeyError:
        return list(REQUIRED_OAUTH_SECRETS)
    except Exception as exc:  # pragma: no cover - defensive logging only
        logger.warning("Unable to read Streamlit auth secrets", error=str(exc))
        return list(REQUIRED_OAUTH_SECRETS)

    missing_keys = [key for key in REQUIRED_OAUTH_SECRETS if not auth_section.get(key)]
    return missing_keys


def render_oauth_signin() -> None:
    """Render native Google Sign-in using st.login()."""
    st.markdown("### 🔐 Welcome to AIPPRO Badging System")
    st.markdown("Sign in with your Google account to access the system.")
    st.markdown("---")

    # Check if OAuth authentication just completed
    oauth_service = get_oauth_service()

    # Check if user is authenticated via OAuth
    if oauth_service.is_authenticated():
        # User authenticated - sync with database and return
        user = oauth_service.get_current_user()
        if user:
            logger.info("OAuth user authenticated", user_id=str(user.id), email=user.email)
            st.success(f"✅ Signed in successfully as {user.email}")
            st.rerun()
        else:
            st.error("Failed to sync user data. Please try signing in again.")
            if hasattr(st, 'logout'):
                st.logout()
    else:
        # User not authenticated, show sign-in options
        from app.core.config import get_settings
        settings = get_settings()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Sign In")
            missing_config = _get_missing_oauth_config_keys()

            if missing_config:
                logger.warning(
                    "Streamlit OAuth configuration missing required secrets",
                    missing_keys=sorted(missing_config),
                )
                st.error(
                    "⚙️ Native OAuth is not configured for this deployment. "
                    "Missing secrets: " + ", ".join(sorted(missing_config))
                )
                st.info(
                    "Set the corresponding `STREAMLIT_AUTH_*` environment variables "
                    "(see `RENDER_SECRETS_SETUP.md`) and redeploy."
                )
            elif hasattr(st, 'login'):
                if st.button("🚀 Sign in with Google", type="primary", use_container_width=True, key="google_signin"):
                    try:
                        st.login()
                    except StreamlitAuthError as exc:
                        logger.error(
                            "Streamlit OAuth login failed due to configuration",
                            error=str(exc),
                        )
                        st.error(
                            "Authentication provider rejected the request. "
                            "Please verify Streamlit auth secrets and try again."
                        )
            else:
                st.error("⚠️ Streamlit OAuth not available. Please ensure Streamlit 1.42+ is installed.")
                st.code("pip install streamlit>=1.42.0 Authlib>=1.3.2")

            st.markdown("---")
            st.info("""
            **About the Sign-In Process:**
            - All users sign in with their Google account
            - New users will complete a quick registration after signing in
            - Existing users will be directed to their dashboard
            """)

        with col2:
            # Development/testing options - only if explicitly enabled
            if settings.enable_mock_auth:
                st.markdown("#### Development Mode")
                if st.button("🧪 Mock OAuth", type="secondary", use_container_width=True):
                    st.session_state.use_mock_oauth = True
                    st.rerun()

    # Handle mock OAuth if enabled
    if st.session_state.get("use_mock_oauth", False):
        render_mock_oauth_form()


def render_mock_oauth_form() -> None:
    """Render mock OAuth form for development/testing."""
    st.markdown("---")
    st.markdown("#### 🧪 Mock OAuth Authentication")
    st.info("This is for development and testing purposes only.")

    with st.form("mock_oauth_form"):
        email = st.text_input(
            "Email Address",
            value="oauth-test@example.com",
            help="Use admin@example.com for admin access"
        )

        name = st.text_input(
            "Display Name",
            value="OAuth Test User",
            help="Name to display in the application"
        )

        submitted = st.form_submit_button("🔑 Mock Sign In", type="primary")

        if submitted and email:
            try:
                # Create mock OAuth service
                mock_service = OAuth2MockService({
                    'sub': f'mock_oauth_{hash(email)}',
                    'email': email,
                    'name': name,
                    'email_verified': True,
                    'iss': 'accounts.google.com'
                })

                # Simulate login (syncs with database, but don't cache in session)
                user = mock_service.mock_login()
                st.session_state.use_mock_oauth = False

                logger.info("Mock OAuth user authenticated", user_id=str(user.id), email=user.email)
                st.success(f"Mock sign-in successful! Welcome, {user.email}")
                st.rerun()

            except Exception as e:
                logger.error("Mock OAuth authentication failed", error=str(e), email=email)
                st.error(f"Mock authentication failed: {str(e)}")

    # Option to go back to real OAuth
    if st.button("← Back to Real OAuth", type="secondary"):
        st.session_state.use_mock_oauth = False
        st.rerun()


def render_oauth_user_info(user: User) -> None:
    """Render user info from OAuth authentication with database integration."""
    oauth_service = get_oauth_service()

    with st.sidebar:
        st.markdown("### 👤 User Information")

        # Basic user information
        st.write(f"**Email:** {user.email}")
        st.write(f"**Role:** {user.role.value}")
        st.write(f"**Status:** {'Active' if user.is_active else 'Inactive'}")

        # Display name if available
        if user.username:
            st.write(f"**Name:** {user.username}")

        # Last login information
        if user.last_login_at:
            st.write(f"**Last Login:** {user.last_login_at.strftime('%Y-%m-%d %H:%M')}")

        # Authentication method indicator
        oauth_service = get_oauth_service()
        if oauth_service.is_authenticated():
            st.success("🔐 Google OAuth")
        else:
            st.info("🎭 Mock Auth (Dev)")

        st.markdown("---")

        # Sign out button
        if st.button("Sign Out", type="secondary"):
            # Clear any session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            # Sign out from OAuth if available
            oauth_service = get_oauth_service()
            if hasattr(st, 'logout') and oauth_service.is_authenticated():
                logger.info("User signing out", user_id=str(user.id), email=user.email)
                st.logout()
            else:
                logger.info("User signed out", user_id=str(user.id), email=user.email)
                st.rerun()


def get_current_oauth_user() -> User | None:
    """
    Get the currently authenticated OAuth user.

    Fetches fresh user data from OAuth service on each call - no caching.
    This ensures proper OAuth session management and security.
    """
    oauth_service = get_oauth_service()
    return oauth_service.get_current_user()


def require_oauth_authentication() -> User | None:
    """Require OAuth authentication and return current user or show sign-in form."""
    user = get_current_oauth_user()

    if user is None:
        render_oauth_signin()
        st.stop()

    return user


def require_oauth_admin() -> User:
    """Require OAuth admin authentication and return current user."""
    user = require_oauth_authentication()

    if user.role.value != "ADMIN":
        st.error("🚫 Access denied. Admin privileges required.")
        st.stop()

    return user


def is_oauth_available() -> bool:
    """Check if Streamlit OAuth functionality is available."""
    return hasattr(st, 'login') and hasattr(st, 'logout') and hasattr(st, 'user')
