"""Main entry point for the AIPPRO Badging System Streamlit application."""

import streamlit as st

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.ui.auth import get_current_user, require_authentication, render_user_info
from app.ui.oauth_auth import (
    get_current_oauth_user, 
    require_oauth_authentication, 
    render_oauth_user_info,
    is_oauth_available
)


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
    
    # Determine authentication method and get user
    settings = get_settings()
    
    # Phase 2B: Try OAuth authentication first if available
    if is_oauth_available():
        user = get_current_oauth_user()
        auth_method = "oauth"
    else:
        # Fallback to Phase 2A authentication
        user = get_current_user() 
        auth_method = "legacy"
    
    if user:
        # User is authenticated - show main application
        if auth_method == "oauth":
            render_oauth_user_info(user)
        else:
            render_user_info(user)
        
        st.write(f"Welcome back, {user.email}!")
        
        if user.role.value == "ADMIN":
            st.success("🔑 You have administrator privileges")
        
        st.markdown("### 📋 Available Features")
        
        # Phase 2B features
        st.info("✅ **Phase 2B Complete**: Real Google OAuth Integration")
        st.write("- Native Streamlit OAuth authentication")
        st.write("- Google Sign-in with st.login()") 
        st.write("- User synchronization with database")
        st.write("- Role-based access control")
        st.write("- Admin bootstrap via environment variables")
        
        # Phase 2A legacy features
        with st.expander("📜 Phase 2A Features (Legacy)"):
            st.write("- Mock authentication system")
            st.write("- User database management")
            st.write("- Session state management")
        
        # Future phases preview
        st.markdown("### 🚀 Coming Soon")
        st.write("**Phase 2C**: Enhanced security features")
        st.write("**Phase 3**: Badge definitions and criteria")
        st.write("**Phase 4**: Badge approval workflows")
        st.write("**Phase 5**: Student self-service portal")
        
        # Development info
        if settings.debug:
            st.markdown("---")
            st.markdown("### 🔧 Development Information")
            st.write(f"**Authentication Method:** {auth_method}")
            st.write(f"**OAuth Available:** {is_oauth_available()}")
            st.write(f"**Streamlit Version:** {st.__version__}")
            
    else:
        # User not authenticated - require sign-in based on available method
        st.write("Welcome to the AIPPRO Digital Badging System")
        st.markdown("This system helps manage digital badges for AI/Pro program participants.")
        
        if is_oauth_available():
            # Use OAuth authentication (Phase 2B)
            require_oauth_authentication()
        else:
            # Fallback to legacy authentication (Phase 2A)
            st.warning("⚠️ Native OAuth not available. Using legacy authentication.")
            require_authentication()

    # Health check endpoint (accessible via query params)
    if st.query_params.get("health"):
        st.json({"status": "healthy", "version": "0.1.0", "phase": "1"})


if __name__ == "__main__":
    main()
