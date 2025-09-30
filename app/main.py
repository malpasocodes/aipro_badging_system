"""Main entry point for the AIPPRO Badging System Streamlit application."""

import streamlit as st

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.ui.auth import get_current_user, require_authentication, render_user_info


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

    # Application header
    st.title("🏆 AIPPRO Badging System")
    
    # Check authentication status
    user = get_current_user()
    
    if user:
        # User is authenticated - show main application
        render_user_info(user)
        
        st.write(f"Welcome back, {user.email}!")
        
        if user.role.value == "ADMIN":
            st.success("🔑 You have administrator privileges")
        
        st.markdown("### 📋 Available Features")
        
        # Phase 2A features
        st.info("✅ **Phase 2A Complete**: Authentication & User Management")
        st.write("- Google Sign-in integration")
        st.write("- Role-based access control") 
        st.write("- Admin bootstrap via environment variables")
        
        # Future phases preview
        st.markdown("### 🚀 Coming Soon")
        st.write("**Phase 2B**: Session management and security")
        st.write("**Phase 3**: Badge definitions and criteria")
        st.write("**Phase 4**: Badge approval workflows")
        st.write("**Phase 5**: Student self-service portal")
        
    else:
        # User not authenticated - require sign-in
        st.write("Welcome to the AIPPRO Digital Badging System")
        st.markdown("This system helps manage digital badges for AI/Pro program participants.")
        require_authentication()

    # Health check endpoint (accessible via query params)
    if st.query_params.get("health"):
        st.json({"status": "healthy", "version": "0.1.0", "phase": "1"})


if __name__ == "__main__":
    main()
