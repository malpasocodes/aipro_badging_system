"""OAuth authentication UI components using Streamlit native authentication."""

import streamlit as st
from typing import Optional

from app.services.oauth import get_oauth_service, OAuth2MockService
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


def render_oauth_signin() -> None:
    """Render native Google Sign-in using st.login()."""
    st.markdown("### 🔐 Sign In")
    st.markdown("Please sign in with your Google account to access the badging system.")
    
    # Check if user is already authenticated
    oauth_service = get_oauth_service()
    
    if oauth_service.is_authenticated():
        # User is authenticated, sync with database
        user = oauth_service.get_current_user()
        if user:
            st.session_state.current_user = user
            st.session_state.auth_method = "oauth"
            logger.info("OAuth user authenticated", user_id=str(user.id), email=user.email)
            st.success(f"Welcome, {user.email}! You are signed in as {user.role.value.lower()}.")
            st.rerun()
        else:
            st.error("Failed to sync user data. Please try signing in again.")
            if hasattr(st, 'logout'):
                st.logout()
    else:
        # User not authenticated, show sign-in options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Production Authentication")
            if hasattr(st, 'login'):
                if st.button("🚀 Sign in with Google", type="primary", use_container_width=True):
                    st.login()
            else:
                st.error("⚠️ Streamlit OAuth not available. Please ensure Streamlit 1.42+ is installed.")
                st.code("pip install streamlit>=1.42.0 Authlib>=1.3.2")
        
        with col2:
            # Development/testing options
            if st.secrets.get("general", {}).get("debug", False):
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
                
                # Simulate login
                user = mock_service.mock_login()
                
                # Store in session
                st.session_state.current_user = user
                st.session_state.auth_method = "mock_oauth"
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
        auth_method = st.session_state.get("auth_method", "unknown")
        if auth_method == "oauth":
            st.success("🔐 Google OAuth")
        elif auth_method == "mock_oauth":
            st.warning("🧪 Mock OAuth (Dev)")
        elif auth_method == "mock":
            st.info("🎭 Mock Auth (Legacy)")
        
        # OAuth user data (for debugging in development)
        if st.secrets.get("general", {}).get("debug", False):
            with st.expander("🔍 Debug: OAuth Data"):
                oauth_data = oauth_service.get_oauth_user_info()
                if oauth_data:
                    st.json(oauth_data)
        
        st.markdown("---")
        
        # Sign out button
        if st.button("Sign Out", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                if key.startswith(('current_user', 'auth_method', 'use_mock')):
                    del st.session_state[key]
            
            # Sign out from OAuth if available
            if hasattr(st, 'logout') and auth_method == "oauth":
                st.logout()
            else:
                logger.info("User signed out", user_id=str(user.id), email=user.email)
                st.success("You have been signed out.")
                st.rerun()


def get_current_oauth_user() -> Optional[User]:
    """Get the currently authenticated OAuth user."""
    # Check session state first
    if 'current_user' in st.session_state:
        return st.session_state.current_user
    
    # Try to get from OAuth service
    oauth_service = get_oauth_service()
    user = oauth_service.get_current_user()
    
    if user:
        st.session_state.current_user = user
        st.session_state.auth_method = "oauth"
    
    return user


def require_oauth_authentication() -> Optional[User]:
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