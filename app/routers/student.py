"""Student dashboard and badge pages."""

import streamlit as st

from app.models.user import User
from app.ui.catalog_browser import render_catalog_browser
from app.ui.progress_dashboard import render_my_badges, render_my_progress
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
        if st.button("📝 Load Request Form", key="load_request_form"):
            render_request_form(user)

    # My Requests (NEW in Phase 4)
    with st.expander("📋 My Badge Requests", expanded=False):
        if st.button("📋 Load My Requests", key="load_my_requests"):
            render_user_requests(user)

    # My Badges - NEW in Phase 6
    with st.expander("🏆 My Badges", expanded=False):
        if st.button("🏆 Load My Badges", key="load_my_badges"):
            render_my_badges(user)

    # My Progress - NEW in Phase 6
    with st.expander("📈 My Progress", expanded=False):
        if st.button("📈 Load My Progress", key="load_my_progress"):
            render_my_progress(user)

    # Available Badges - Phase 5
    with st.expander("📚 Browse Badge Catalog", expanded=False):
        if st.button("📚 Load Badge Catalog", key="load_badge_catalog"):
            render_catalog_browser(user)

    # Getting Started Guide
    st.markdown("---")
    st.markdown("### 🚀 How It Works")

    st.info("""
    **Welcome to the AIPPRO Badging System!**

    Ready to start earning badges? Here's how:

    1. **📚 Explore** - Browse available badges and programs in the catalog
    2. **📝 Request** - Submit badge requests when you've mastered a skill
    3. **⏳ Wait** - Admins/Assistants review and approve your requests
    4. **🏅 Earn** - Badges are automatically awarded upon approval
    5. **📈 Progress** - Complete badges → earn skills → complete programs!
    6. **🏆 Celebrate** - Track your achievements and share your success

    **Automatic Progression:** When you earn all mini-badges in a skill, you automatically
    earn the skill badge. Complete all skills in a program to earn the program badge!
    """)

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
