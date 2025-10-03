"""Main entry point for the AIPPRO Badging System Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure absolute imports work when Streamlit executes this file directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.models.user import UserRole
from app.routers import (
    render_admin_dashboard,
    render_assistant_dashboard,
    render_student_dashboard,
)
from app.services.onboarding import get_onboarding_service
from app.ui.auth import get_current_user, render_user_info, require_authentication
from app.ui.oauth_auth import (
    get_current_oauth_user,
    is_oauth_available,
    render_oauth_user_info,
    require_oauth_authentication,
)
from app.ui.onboarding import render_onboarding_form


def main() -> None:
    """Main application entry point."""
    # Initialize logging
    setup_logging()

    # Load configuration (will be used in future phases)
    _ = get_settings()

    # Set page configuration
    st.set_page_config(
        page_title="AIPPRO Badging System",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Get settings
    settings = get_settings()

    # Check if user is authenticated via OAuth
    # Phase 2B: Try OAuth authentication first if available
    # No session caching - always fetch from OAuth for security
    if is_oauth_available():
        user = get_current_oauth_user()
    else:
        # Fallback to Phase 2A authentication
        user = get_current_user()

    # If no authenticated user, show login page
    if not user:
        # User not authenticated - show login page
        st.title("🏆 AIPPRO Badging System")
        st.markdown("---")

        if is_oauth_available():
            # Use OAuth authentication (Phase 2B)
            require_oauth_authentication()
        else:
            # Fallback to legacy authentication (Phase 2A)
            st.warning("⚠️ Native OAuth not available. Using legacy authentication.")
            require_authentication()
        st.stop()

    # User is authenticated - show application header
    st.title("🏆 AIPPRO Badging System")

    if user:
        # Phase 3: Check if user has completed registration/onboarding
        onboarding_service = get_onboarding_service()
        if not onboarding_service.check_onboarding_status(user):
            # User needs to complete registration (applies to all roles)
            render_onboarding_form()
            return

        # User is authenticated and registered - show user info in sidebar
        if is_oauth_available():
            render_oauth_user_info(user)
        else:
            render_user_info(user)

        # Route to role-specific dashboard
        if user.role == UserRole.ADMIN:
            render_admin_dashboard(user)
        elif user.role == UserRole.ASSISTANT:
            render_assistant_dashboard(user)
        elif user.role == UserRole.STUDENT:
            render_student_dashboard(user)
        else:
            # Fallback for unknown roles
            st.error(f"Unknown user role: {user.role}")
            st.write("Please contact an administrator.")

        # Development info (shown for all roles in debug mode)
        if settings.debug:
            st.markdown("---")
            st.markdown("### 🔧 Development Information")
            st.write(f"**User ID:** {user.id}")
            st.write(f"**Role:** {user.role.value}")
            st.write(f"**OAuth Available:** {is_oauth_available()}")
            st.write(f"**Streamlit Version:** {st.__version__}")
            st.write(f"**Onboarded:** {user.is_onboarded()}")

    # Health check endpoint (accessible via query params)
    if st.query_params.get("health"):
        st.json({"status": "healthy", "version": "0.3.0", "phase": "3"})


if __name__ == "__main__":
    main()
