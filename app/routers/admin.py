"""Admin dashboard and management pages."""

import streamlit as st

from app.models.user import User


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

    # User Management section
    with st.expander("👥 User Management", expanded=True):
        st.info("**Coming in Phase 4**: Manage users, roles, and permissions")
        st.markdown("""
        **Planned Features:**
        - View all users (students, assistants, admins)
        - Assign and modify user roles
        - Activate/deactivate user accounts
        - View user activity and login history
        - Export user roster with PII redaction options
        """)

    # Badge Catalog Management
    with st.expander("🏆 Badge Catalog Management"):
        st.info("**Coming in Phase 5**: Manage badge hierarchy and criteria")
        st.markdown("""
        **Planned Features:**
        - Create and edit badge programs
        - Define skills and mini-badges
        - Set badge criteria and requirements
        - Retire or archive badges
        - View badge statistics and distribution
        """)

    # Approval Queue (Admin can approve too)
    with st.expander("✅ Approval Queue"):
        st.info("**Coming in Phase 4**: Review and approve badge requests")
        st.markdown("""
        **Planned Features:**
        - View pending badge requests
        - Approve or reject requests with notes
        - Bulk approval actions
        - View approval history
        - Assign requests to assistants
        """)

    # System Administration
    with st.expander("⚙️ System Administration"):
        st.info("**Coming in Phase 8+**: System configuration and exports")
        st.markdown("""
        **Planned Features:**
        - Configure system settings
        - Manage admin and assistant accounts
        - Export audit logs
        - Export badge data with PII redaction
        - View system health and statistics
        """)

    # Quick Stats (Placeholder)
    st.markdown("---")
    st.markdown("### 📊 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Users", "—", help="Coming in Phase 4")

    with col2:
        st.metric("Active Badges", "—", help="Coming in Phase 5")

    with col3:
        st.metric("Pending Requests", "—", help="Coming in Phase 4")

    with col4:
        st.metric("Badges Awarded", "—", help="Coming in Phase 6")

    # Current Phase Information
    st.markdown("---")
    st.markdown("### ✅ Completed Phases")

    st.success("**Phase 1**: Project Setup & Repository Initialization")
    st.success("**Phase 2A**: Mock Authentication System")
    st.success("**Phase 2B**: Real Google OAuth Integration")
    st.success("**Phase 3**: User Onboarding & Registration")

    st.markdown("### 🚀 Upcoming Phases")
    st.write("**Phase 4**: Roles & Approvals Queue")
    st.write("**Phase 5**: Badge Data Model & Catalog")
    st.write("**Phase 6**: Earning Logic & Awards")
    st.write("**Phase 7**: Notifications & Audit Trails")
    st.write("**Phase 8**: Exports & PII Redaction")
    st.write("**Phase 9**: UX Polish & Accessibility")
    st.write("**Phase 10**: Deployment & Launch")
