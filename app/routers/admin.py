"""Admin dashboard and management pages."""

import streamlit as st

from app.models.user import User
from app.ui.approval_queue import render_approval_queue
from app.ui.award_management import render_award_management
from app.ui.catalog_management import render_catalog_management
from app.ui.roster import render_roster


def render_admin_dashboard(user: User) -> None:
    """
    Render admin dashboard with user management and system controls.

    Args:
        user: Authenticated admin user
    """
    st.markdown("## 👑 Admin Dashboard")
    st.markdown(f"Welcome back, **{user.username or user.email}**!")
    st.markdown("---")

    # Admin-specific features
    st.markdown("### 🔧 Admin Functions")

    # User Management section - NEW in Phase 4 (with role editing)
    with st.expander("👥 User Management", expanded=False):
        if st.button("📊 Load User Management", key="load_user_mgmt"):
            render_roster(user, can_edit_roles=True)

    # Approval Queue (Admin can approve too) - NEW in Phase 4
    with st.expander("✅ Approval Queue"):
        if st.button("📋 Load Approval Queue", key="load_approval_queue"):
            render_approval_queue(user)

    # Badge Catalog Management - NEW in Phase 5
    with st.expander("📚 Badge Catalog Management"):
        if st.button("📚 Load Catalog Management", key="load_catalog_mgmt"):
            render_catalog_management(user)

    # Award Management - NEW in Phase 6
    with st.expander("🏆 Award Management"):
        if st.button("🏆 Load Award Management", key="load_award_mgmt"):
            render_award_management(user)

    # System Administration
    with st.expander("⚙️ System Administration"):
        st.info("**Coming in Phase 7-8**: System configuration and exports")
        st.markdown("""
        **Planned Features:**
        - View notifications and audit trails (Phase 7)
        - Export audit logs with PII redaction (Phase 8)
        - Export badge data with PII redaction (Phase 8)
        - Configure system settings
        - View system health and statistics
        """)

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
