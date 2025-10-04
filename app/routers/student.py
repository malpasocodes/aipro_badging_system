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

    # Sidebar controls for badge journey
    with st.sidebar:
        st.markdown("### 🏅 Your Badge Journey")

        if st.button("📝 Request a Badge", key="btn_request_badge", use_container_width=True):
            st.session_state.student_active_panel = "request_form"

        if st.button("📋 My Badge Requests", key="btn_my_requests", use_container_width=True):
            st.session_state.student_active_panel = "requests"

        if st.button("🏆 My Badges", key="btn_my_badges", use_container_width=True):
            st.session_state.student_active_panel = "my_badges"

        if st.button("📈 My Progress", key="btn_my_progress", use_container_width=True):
            st.session_state.student_active_panel = "my_progress"

        if st.button("📚 Browse Badge Catalog", key="btn_badge_catalog", use_container_width=True):
            st.session_state.student_active_panel = "catalog"

    # Render selected panel
    active_panel = st.session_state.get("student_active_panel")

    if active_panel == "request_form":
        st.markdown("### 📝 Request a Badge")
        render_request_form(user)
    elif active_panel == "requests":
        st.markdown("### 📋 My Badge Requests")
        render_user_requests(user)
    elif active_panel == "my_badges":
        st.markdown("### 🏆 My Badges")
        render_my_badges(user)
    elif active_panel == "my_progress":
        st.markdown("### 📈 My Progress")
        render_my_progress(user)
    elif active_panel == "catalog":
        st.markdown("### 📚 Browse Badge Catalog")
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
