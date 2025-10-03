"""Student progress dashboard UI components."""

from uuid import UUID

import streamlit as st

from app.models.award import AwardType
from app.models.user import User
from app.services.catalog_service import get_catalog_service
from app.services.progress_service import get_progress_service
from app.ui.badge_display import (
    render_award_badge,
    render_mini_badge_list,
    render_program_card,
    render_progress_summary,
    render_skill_card,
)


def render_my_badges(user: User) -> None:
    """
    Render earned badges section.

    Args:
        user: Current user
    """
    st.markdown("### 🏆 My Earned Badges")

    progress_service = get_progress_service()

    # Get all user awards
    awards = progress_service.get_user_awards(user.id)

    if not awards:
        st.info("You haven't earned any badges yet. Submit badge requests to get started!")
        return

    # Organize awards by type
    mini_badges = [a for a in awards if a.award_type == AwardType.MINI_BADGE]
    skills = [a for a in awards if a.award_type == AwardType.SKILL]
    programs = [a for a in awards if a.award_type == AwardType.PROGRAM]

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🏅 Mini-Badges", len(mini_badges))

    with col2:
        st.metric("⭐ Skills", len(skills))

    with col3:
        st.metric("🏆 Programs", len(programs))

    st.markdown("---")

    # Tabs for different award types
    tab1, tab2, tab3 = st.tabs(["🏅 Mini-Badges", "⭐ Skills", "🏆 Programs"])

    with tab1:
        if mini_badges:
            st.markdown(f"**{len(mini_badges)} mini-badge(s) earned**")
            st.markdown("---")
            for award in sorted(mini_badges, key=lambda a: a.awarded_at, reverse=True):
                render_award_badge(award)
        else:
            st.info("No mini-badges earned yet")

    with tab2:
        if skills:
            st.markdown(f"**{len(skills)} skill(s) mastered**")
            st.markdown("---")
            for award in sorted(skills, key=lambda a: a.awarded_at, reverse=True):
                render_award_badge(award)
        else:
            st.info("No skills earned yet")

    with tab3:
        if programs:
            st.markdown(f"**{len(programs)} program(s) completed**")
            st.markdown("---")
            for award in sorted(programs, key=lambda a: a.awarded_at, reverse=True):
                render_award_badge(award)
        else:
            st.info("No programs completed yet")


def render_my_progress(user: User) -> None:
    """
    Render progress tracking section with skill and program progress.

    Args:
        user: Current user
    """
    st.markdown("### 📈 My Progress")

    progress_service = get_progress_service()
    catalog_service = get_catalog_service()

    # Get all progress data
    all_progress = progress_service.get_all_progress(user.id)

    if not all_progress:
        st.info("No progress data available. Browse the badge catalog to see available programs.")
        return

    # Calculate overall statistics
    total_programs = len(all_progress)
    earned_programs = sum(1 for p in all_progress if p.get("program_earned"))

    total_skills = sum(p["total_skills"] for p in all_progress)
    earned_skills = sum(p["earned_skills"] for p in all_progress)

    total_mini_badges = sum(p["total_mini_badges"] for p in all_progress)
    earned_mini_badges = sum(p["earned_mini_badges"] for p in all_progress)

    # Render overall summary
    render_progress_summary(
        total_mini_badges=total_mini_badges,
        earned_mini_badges=earned_mini_badges,
        total_skills=total_skills,
        earned_skills=earned_skills,
        total_programs=total_programs,
        earned_programs=earned_programs,
    )

    # Render each program's progress
    st.markdown("### 📚 Programs")

    # Filter options
    filter_option = st.radio(
        "Show:",
        ["All Programs", "In Progress", "Completed", "Not Started"],
        horizontal=True,
        label_visibility="collapsed"
    )

    for prog_data in all_progress:
        program_earned = prog_data.get("program_earned", False)
        progress_percent = prog_data.get("progress_percent", 0)

        # Apply filter
        if filter_option == "In Progress" and (program_earned or progress_percent == 0) or filter_option == "Completed" and not program_earned or filter_option == "Not Started" and progress_percent > 0:
            continue

        # Render program card
        render_program_card(
            program_title=prog_data["program_title"],
            description=prog_data.get("program_description"),
            earned=program_earned,
            progress_percent=progress_percent,
            skill_count=prog_data["total_skills"],
            earned_skills=prog_data["earned_skills"],
            earned_date=prog_data.get("program_earned_at"),
        )

        # Show detailed skill progress in expander
        if prog_data["skills"]:
            with st.expander(f"View Skills ({prog_data['earned_skills']}/{prog_data['total_skills']} complete)"):
                for skill_data in prog_data["skills"]:
                    render_skill_card(
                        skill_title=skill_data["skill_title"],
                        earned=skill_data.get("skill_earned", False),
                        progress_percent=skill_data.get("progress_percent", 0),
                        mini_badge_count=skill_data["total_mini_badges"],
                        earned_date=skill_data.get("skill_earned_at"),
                    )

                    # Show mini-badge details
                    if skill_data.get("mini_badges"):
                        with st.expander(f"Mini-Badges ({skill_data['earned_mini_badges']}/{skill_data['total_mini_badges']})"):
                            render_mini_badge_list(
                                skill_data["mini_badges"],
                                show_progress=False
                            )


def render_skill_detail(user: User, skill_id: UUID) -> None:
    """
    Render detailed progress for a specific skill.

    Args:
        user: Current user
        skill_id: ID of skill to display
    """
    progress_service = get_progress_service()
    catalog_service = get_catalog_service()

    # Get skill from catalog
    skill = catalog_service.get_skill(skill_id)
    if not skill:
        st.error("Skill not found")
        return

    # Get progress data
    progress_data = progress_service.get_skill_progress(user.id, skill_id)

    st.markdown(f"## ⭐ {skill.title}")
    if skill.description:
        st.caption(skill.description)

    st.markdown("---")

    # Progress overview
    earned_count = progress_data["earned_count"]
    total_count = progress_data["total_count"]
    percentage = progress_data["percentage"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.progress(percentage / 100.0)
        st.caption(f"{earned_count} of {total_count} mini-badges earned ({percentage}%)")

    with col2:
        if percentage == 100:
            st.success("✅ Skill Earned!")
        elif percentage > 0:
            st.info(f"🔄 {percentage}% Complete")
        else:
            st.caption("⏳ Not Started")

    st.markdown("---")

    # Mini-badges list
    st.markdown("### 🏅 Mini-Badges")
    render_mini_badge_list(progress_data["mini_badges"], show_progress=False)


def render_program_detail(user: User, program_id: UUID) -> None:
    """
    Render detailed progress for a specific program.

    Args:
        user: Current user
        program_id: ID of program to display
    """
    progress_service = get_progress_service()
    catalog_service = get_catalog_service()

    # Get program from catalog
    program = catalog_service.get_program(program_id)
    if not program:
        st.error("Program not found")
        return

    # Get progress data
    progress_data = progress_service.get_program_progress(user.id, program_id)

    st.markdown(f"## 🏆 {program.title}")
    if program.description:
        st.caption(program.description)

    st.markdown("---")

    # Progress overview
    earned_skills = progress_data["earned_skills"]
    total_skills = progress_data["total_skills"]
    percentage = progress_data["progress_percent"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.progress(percentage / 100.0)
        st.caption(f"{earned_skills} of {total_skills} skills mastered ({percentage}%)")

    with col2:
        if percentage == 100:
            st.success("✅ Program Complete!")
        elif percentage > 0:
            st.info(f"🔄 {percentage}% Complete")
        else:
            st.caption("⏳ Not Started")

    st.markdown("---")

    # Skills list
    st.markdown("### ⭐ Skills")

    for skill_data in progress_data["skills"]:
        with st.expander(
            f"{'✅' if skill_data.get('earned') else '⏳'} {skill_data['title']} ({skill_data.get('progress_percent', 0)}%)",
            expanded=False
        ):
            if skill_data.get("description"):
                st.caption(skill_data["description"])

            # Mini-badges in this skill
            mini_badges = catalog_service.get_mini_badges_by_skill(skill_data["skill_id"])
            if mini_badges:
                st.markdown(f"**Mini-Badges:** {len(mini_badges)} total")

                # Get which ones are earned
                user_awards = progress_service.get_user_awards(
                    user.id,
                    award_type=AwardType.MINI_BADGE
                )
                earned_mini_badge_ids = {
                    a.mini_badge_id for a in user_awards if a.mini_badge_id
                }

                mini_badge_list = []
                for mb in mini_badges:
                    mini_badge_list.append({
                        "id": mb.id,
                        "title": mb.title,
                        "description": mb.description,
                        "is_active": mb.is_active,
                        "earned": mb.id in earned_mini_badge_ids,
                        "earned_date": None,  # Could enhance to get actual date
                    })

                render_mini_badge_list(mini_badge_list, show_progress=False)


def render_progress_dashboard(user: User) -> None:
    """
    Main progress dashboard view.

    Args:
        user: Current user
    """
    st.markdown("## 📊 Progress Dashboard")
    st.markdown(f"Welcome, **{user.username}**! Track your learning journey here.")
    st.markdown("---")

    # Main tabs
    tab1, tab2 = st.tabs(["🏆 My Badges", "📈 My Progress"])

    with tab1:
        render_my_badges(user)

    with tab2:
        render_my_progress(user)
