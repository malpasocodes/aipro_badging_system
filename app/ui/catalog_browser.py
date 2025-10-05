"""Student-facing badge catalog browser."""

import streamlit as st

from app.models import User
from app.services import get_catalog_service


def render_catalog_browser(user: User) -> None:
    """
    Render public badge catalog browser for students.

    Shows hierarchical view of programs → skills → mini-badges.
    Students can browse catalog and view badge details.
    """
    st.markdown("## 📚 Badge Catalog")
    st.markdown("Browse available badges and programs")

    catalog_service = get_catalog_service()

    # Get full catalog (active badges only)
    catalog = catalog_service.get_full_catalog()

    if not catalog["programs"]:
        st.info("No badges available yet. Check back soon!")
        return

    # Display programs with expandable skills and mini-badges
    for program in catalog["programs"]:
        with st.expander(f"📖 **{program['title']}**", expanded=False):
            if program["description"]:
                st.markdown(program["description"])

            # Show program stats
            total_skills = len(program["skills"])
            total_mini_badges = sum(len(skill["mini_badges"]) for skill in program["skills"])
            total_progress_badges = len(program.get("progress_badges", []))

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Skills", total_skills)
            with col2:
                st.metric("Mini-badges", total_mini_badges)
            with col3:
                # Future: Show earned count
                st.metric("Your Progress", "—", help="Coming in Phase 6")
            with col4:
                st.metric("Progress Badges", total_progress_badges)

            st.markdown("---")

            # Display skills
            if not program["skills"]:
                st.caption("No skills available yet")
            else:
                for skill in program["skills"]:
                    with st.container():
                        st.markdown(f"### 🎯 {skill['title']}")
                        if skill["description"]:
                            st.caption(skill["description"])

                        # Display mini-badges in this skill
                        if not skill["mini_badges"]:
                            st.caption("_No mini-badges available yet_")
                        else:
                            # Display mini-badges in a grid
                            cols = st.columns(2)
                            for idx, badge in enumerate(skill["mini_badges"]):
                                with cols[idx % 2]:
                                    render_mini_badge_card(badge, user)

                        st.markdown("")  # Spacing

            # Display capstones if any
            if program.get("capstones"):
                st.markdown("---")
                st.markdown("### 🎓 Capstones")

                for capstone in program["capstones"]:
                    required_badge = "⭐" if capstone["is_required"] else "💫"
                    st.markdown(f"**{required_badge} {capstone['title']}** {'(Required)' if capstone['is_required'] else '(Optional)'}")
                    if capstone["description"]:
                        st.caption(capstone["description"])

            if program.get("progress_badges"):
                st.markdown("---")
                st.markdown("### 🚀 Progress Badges")

                for badge in program["progress_badges"]:
                    st.markdown(f"**{badge['icon']} {badge['title']}**")
                    if badge["description"]:
                        st.caption(badge["description"])


def render_mini_badge_card(badge: dict, user: User) -> None:
    """Render a mini-badge card with request button."""
    with st.container():
        # Badge title and description
        st.markdown(f"**🏅 {badge['title']}**")

        if badge["description"]:
            with st.expander("Details"):
                st.markdown(badge["description"])

        # Request button (quick action)
        if st.button("Request", key=f"request_badge_{badge['id']}", use_container_width=True, type="secondary"):
            st.session_state["quick_request_badge_id"] = str(badge["id"])
            st.session_state["quick_request_badge_title"] = badge["title"]
            st.success(f"✅ Navigate to 'Request a Badge' to complete your request for: {badge['title']}")

        st.divider()


def render_catalog_search(user: User) -> None:
    """
    Render searchable catalog view (future enhancement).

    Allows students to search badges by title or description.
    """
    st.markdown("## 🔍 Search Badges")

    search_query = st.text_input("Search by title or description", key="catalog_search")

    if search_query:
        catalog_service = get_catalog_service()

        # Get all mini-badges
        all_badges = catalog_service.list_mini_badges(include_inactive=False)

        # Filter by search query
        matching_badges = [
            badge for badge in all_badges
            if search_query.lower() in badge.title.lower()
            or (badge.description and search_query.lower() in badge.description.lower())
        ]

        if matching_badges:
            st.markdown(f"**Found {len(matching_badges)} badge(s)**")

            for badge in matching_badges:
                # Get parent info
                skill = catalog_service.get_skill(badge.skill_id)
                program = catalog_service.get_program(skill.program_id) if skill else None

                with st.container():
                    st.markdown(f"**🏅 {badge.title}**")
                    st.caption(f"Skill: {skill.title if skill else 'Unknown'} | Program: {program.title if program else 'Unknown'}")

                    if badge.description:
                        st.markdown(badge.description)

                    if st.button("Request", key=f"search_request_{badge.id}", use_container_width=True):
                        st.session_state["quick_request_badge_id"] = str(badge.id)
                        st.session_state["quick_request_badge_title"] = badge.title
                        st.success(f"✅ Navigate to 'Request a Badge' to complete: {badge.title}")

                    st.divider()
        else:
            st.info(f"No badges found matching '{search_query}'")
