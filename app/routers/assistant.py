"""Assistant dashboard and approval pages."""

import streamlit as st

from app.models.user import User


def render_assistant_dashboard(user: User) -> None:
    """
    Render assistant dashboard with badge approval queue.

    Args:
        user: Authenticated assistant user
    """
    st.markdown("## 🎯 Assistant Dashboard")
    st.markdown(f"Welcome back, **{user.username or user.email}**!")
    st.markdown("---")

    # Assistant-specific features
    st.markdown("### ✅ Assistant Functions")

    # Approval Queue (Primary function)
    with st.expander("📋 Badge Approval Queue", expanded=True):
        st.info("**Coming in Phase 4**: Review and approve student badge requests")
        st.markdown("""
        **Planned Features:**
        - View pending badge requests assigned to you
        - Filter requests by badge type, student, or date
        - Review student submissions and evidence
        - Approve or reject requests with feedback notes
        - View your approval history and statistics
        - Bulk actions for common approvals
        """)

    # Student Roster View
    with st.expander("👥 Student Roster"):
        st.info("**Coming in Phase 4**: View students and their progress")
        st.markdown("""
        **Planned Features:**
        - View all students in the program
        - See student badge progress and awards
        - Filter and search students
        - View student contact information
        - Export student roster (with PII redaction)
        """)

    # Badge Information
    with st.expander("🏆 Badge Catalog (Read-Only)"):
        st.info("**Coming in Phase 5**: View badge definitions and criteria")
        st.markdown("""
        **Planned Features:**
        - Browse available badges and programs
        - View badge criteria and requirements
        - See badge descriptions and prerequisites
        - View badge award statistics
        - Search badges by skill or program
        """)

    # My Activity
    with st.expander("📊 My Activity"):
        st.info("**Coming in Phase 7**: Track your approval activity")
        st.markdown("""
        **Planned Features:**
        - View your recent approvals and rejections
        - See approval metrics and statistics
        - View pending items assigned to you
        - Track your response time and workload
        """)

    # Quick Stats (Placeholder)
    st.markdown("---")
    st.markdown("### 📊 My Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pending Reviews", "—", help="Coming in Phase 4")

    with col2:
        st.metric("Approved This Week", "—", help="Coming in Phase 4")

    with col3:
        st.metric("Total Students", "—", help="Coming in Phase 4")

    # Helpful Information
    st.markdown("---")
    st.markdown("### 💡 Assistant Guide")

    st.info("""
    **Your Role as an Assistant:**
    - Review and approve student badge requests
    - Provide constructive feedback on rejections
    - Ensure badge criteria are met before approval
    - Help students understand badge requirements
    - Maintain fair and consistent approval standards
    """)

    # Current Phase Information
    st.markdown("---")
    st.markdown("### ✅ Completed Phases")

    st.success("**Phase 3**: User Onboarding & Registration - You've completed registration!")

    st.markdown("### 🚀 Next Up")
    st.write("**Phase 4**: Approval queue and roster management")
    st.write("**Phase 5**: Badge catalog and criteria")
    st.write("**Phase 6**: Student progress tracking")
