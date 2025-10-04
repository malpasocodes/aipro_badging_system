"""Admin dashboard and management pages."""

import streamlit as st

from app.models.user import User
from app.ui.approval_queue import render_approval_queue
from app.ui.award_management import render_award_management
from app.ui.catalog_management import render_catalog_management
from app.ui.user_management import render_add_delete_user, render_user_roster


def render_admin_dashboard(user: User) -> None:
    """
    Render admin dashboard with user management and system controls.

    Args:
        user: Authenticated admin user
    """
    st.markdown("## 👑 Admin Dashboard")
    st.markdown(f"Welcome back, **{user.username or user.email}**!")
    st.markdown("---")

    # Sidebar controls for admin functions
    with st.sidebar:
        st.markdown("### 🔧 Admin Functions")

        # User management controls
        with st.expander("👥 User Management", expanded=False):
            if st.button(
                "📊 User Roster",
                key="btn_user_roster",
                use_container_width=True,
            ):
                st.session_state.active_user_mgmt_function = "roster"
            if st.button(
                "➕➖ Add / Delete User",
                key="btn_add_delete_user",
                use_container_width=True,
            ):
                st.session_state.active_user_mgmt_function = "add_delete"

        # Approval queue controls
        with st.expander("✅ Approval Queue", expanded=False):
            if st.button("📋 Load Approval Queue", key="load_approval_queue"):
                st.session_state.active_approval_queue = True

        # Catalog management controls
        with st.expander("📚 Badge Catalog Management", expanded=False):
            if st.button("📚 Load Catalog Management", key="load_catalog_mgmt"):
                st.session_state.active_catalog_mgmt = True

        # Award management controls
        with st.expander("🏆 Award Management", expanded=False):
            if st.button("🏆 Load Award Management", key="load_award_mgmt"):
                st.session_state.active_award_mgmt = True

        with st.expander("⚙️ System Administration"):
            st.info("**Coming in Phase 7-8**: System configuration and exports")
            st.markdown(
                """
                **Planned Features:**
                - View notifications and audit trails (Phase 7)
                - Export audit logs with PII redaction (Phase 8)
                - Export badge data with PII redaction (Phase 8)
                - Configure system settings
                - View system health and statistics
                """
            )

    # Render main content based on selections
    active_function = st.session_state.get("active_user_mgmt_function")
    if active_function == "roster":
        st.markdown("### 👥 User Roster")
        render_user_roster(user)
    elif active_function == "add_delete":
        st.markdown("### ➕➖ Add / Delete User")
        render_add_delete_user(user)

    if st.session_state.get("active_approval_queue"):
        st.markdown("### ✅ Approval Queue")
        render_approval_queue(user)

    if st.session_state.get("active_catalog_mgmt"):
        st.markdown("### 📚 Badge Catalog Management")
        render_catalog_management(user)

    if st.session_state.get("active_award_mgmt"):
        st.markdown("### 🏆 Award Management")
        render_award_management(user)

    # Current Phase Information
    st.markdown("---")
    st.markdown("### ✅ Completed Phases")

    st.success("**Phase 1**: Project Setup & Repository Initialization")
    st.success("**Phase 2A**: Mock Authentication System")
    st.success("**Phase 2B**: Real Google OAuth Integration")
    st.success("**Phase 3**: User Onboarding & Registration")
    st.success("**Phase 4**: Roles & Approvals Queue")
    st.success("**Phase 5**: Badge Data Model & Catalog")
    st.success("**Phase 6**: Earning Logic & Awards ✨")

    st.markdown("### 🚀 Upcoming Phases")
    st.write("**Phase 7**: Notifications & Audit Trails")
    st.write("**Phase 8**: Exports & PII Redaction")
    st.write("**Phase 9**: UX Polish & Accessibility")
    st.write("**Phase 10**: Deployment & Launch")
