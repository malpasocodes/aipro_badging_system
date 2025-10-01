"""Student dashboard and badge pages."""

import streamlit as st

from app.models.user import User
from app.ui.catalog_browser import render_catalog_browser
from app.ui.request_form import render_request_form, render_user_requests


def render_student_dashboard(user: User) -> None:
    """
    Render student dashboard with badges and progress.

    Args:
        user: Authenticated student user
    """
    st.markdown("## 🎓 Student Dashboard")
    st.markdown(f"Welcome back, **{user.username}**!")
    st.markdown("---")

    # Student-specific features
    st.markdown("### 🏅 Your Badge Journey")

    # Request a Badge (NEW in Phase 4)
    with st.expander("📝 Request a Badge", expanded=False):
        render_request_form(user)

    # My Requests (NEW in Phase 4)
    with st.expander("📋 My Badge Requests", expanded=True):
        render_user_requests(user)

    # My Badges
    with st.expander("🏆 My Badges"):
        st.info("**Coming in Phase 6**: View your earned badges and progress")
        st.markdown("""
        **Planned Features:**
        - View all your earned badges
        - See badges in progress
        - Track completion percentages
        - View badge award dates
        - Share badge achievements
        - Download badge certificates
        """)

    # Available Badges - NEW in Phase 5
    with st.expander("📚 Browse Badge Catalog", expanded=False):
        render_catalog_browser(user)

    # My Progress
    with st.expander("📈 My Progress"):
        st.info("**Coming in Phase 6**: Track your learning progress")
        st.markdown("""
        **Planned Features:**
        - View progress toward program completion
        - See skill development over time
        - Track badge milestones
        - View progress charts and statistics
        - Compare progress with program goals
        """)

    # Quick Stats (Placeholder)
    st.markdown("---")
    st.markdown("### 📊 Your Progress")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Badges Earned", "—", help="Coming in Phase 6")

    with col2:
        st.metric("In Progress", "—", help="Coming in Phase 6")

    with col3:
        st.metric("Pending Requests", "—", help="Coming in Phase 4")

    with col4:
        st.metric("Programs Complete", "—", help="Coming in Phase 6")

    # Getting Started Guide
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")

    st.info("""
    **Welcome to the AIPPRO Badging System!**

    You've successfully completed registration. Here's what comes next:

    1. **Explore Badges** - Browse available badges and programs (Phase 5)
    2. **Request Badges** - Submit requests with evidence (Phase 4)
    3. **Track Progress** - Monitor your badge journey (Phase 6)
    4. **Earn Recognition** - Collect badges as you master skills

    Stay tuned for these features in upcoming releases!
    """)

    # Current Phase Information
    st.markdown("---")
    st.markdown("### ✅ Registration Complete!")

    st.success("You've completed Phase 3: User Onboarding & Registration")
    st.markdown("""
    Your profile is set up and you're ready to start earning badges once the system is fully launched.
    """)

    st.markdown("### 🚀 Coming Soon")
    st.write("**Phase 4**: Request badges and track approvals")
    st.write("**Phase 5**: Browse the complete badge catalog")
    st.write("**Phase 6**: Earn badges and track your progress")
    st.write("**Phase 7**: Receive notifications for approvals and awards")

    # Helpful Tips
    st.markdown("---")
    st.markdown("### 💡 Tips for Success")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Badge Best Practices:**
        - Read requirements carefully
        - Gather evidence before requesting
        - Provide clear documentation
        - Follow up on feedback
        """)

    with col2:
        st.markdown("""
        **Program Completion:**
        - Focus on foundational skills first
        - Build toward program goals
        - Track your prerequisites
        - Celebrate milestones!
        """)
