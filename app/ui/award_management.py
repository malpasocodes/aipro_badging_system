"""Admin award management UI components."""

from uuid import UUID

import streamlit as st

from app.models.award import AwardType
from app.models.user import User, UserRole
from app.services.catalog_service import get_catalog_service
from app.services.progress_service import get_progress_service, ProgressError
from app.ui.badge_display import render_award_badge


def render_award_management(admin_user: User) -> None:
    """
    Render admin award management interface.

    Args:
        admin_user: Admin user performing award management
    """
    if admin_user.role not in (UserRole.ADMIN, UserRole.ASSISTANT):
        st.error("Unauthorized: Only admins and assistants can manage awards")
        return

    st.markdown("## 🏆 Award Management")
    st.markdown("Manually award badges and view award statistics.")
    st.markdown("---")

    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs([
        "📊 Award Statistics",
        "🎖️ Manual Award",
        "🔍 View User Awards"
    ])

    with tab1:
        render_award_statistics()

    with tab2:
        render_manual_award_form(admin_user)

    with tab3:
        render_user_award_viewer()


def render_award_statistics() -> None:
    """Render overall award statistics."""
    st.markdown("### 📊 Award Statistics")

    progress_service = get_progress_service()

    # Get all awards (across all users)
    # Note: This is a simplified approach. For production, add a method to ProgressService
    # to get aggregate statistics without loading all awards.
    from app.core.database import get_engine
    from sqlmodel import Session, select, func
    from app.models.award import Award

    engine = get_engine()

    with Session(engine) as session:
        # Total awards by type
        mini_badge_count = session.exec(
            select(func.count(Award.id)).where(Award.award_type == AwardType.MINI_BADGE)
        ).one()

        skill_count = session.exec(
            select(func.count(Award.id)).where(Award.award_type == AwardType.SKILL)
        ).one()

        program_count = session.exec(
            select(func.count(Award.id)).where(Award.award_type == AwardType.PROGRAM)
        ).one()

        # Automatic vs manual awards
        automatic_count = session.exec(
            select(func.count(Award.id)).where(Award.awarded_by == None)
        ).one()

        manual_count = session.exec(
            select(func.count(Award.id)).where(Award.awarded_by != None)
        ).one()

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🏅 Mini-Badges Awarded", mini_badge_count)

    with col2:
        st.metric("⭐ Skills Awarded", skill_count)

    with col3:
        st.metric("🏆 Programs Awarded", program_count)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🤖 Automatic Awards", automatic_count, help="Triggered by progression logic")

    with col2:
        st.metric("👤 Manual Awards", manual_count, help="Awarded by admins/assistants")


def render_manual_award_form(admin_user: User) -> None:
    """
    Render form for manually awarding badges.

    Args:
        admin_user: Admin user awarding the badge
    """
    st.markdown("### 🎖️ Manual Award")
    st.info("Manually award a badge to a student. This is useful for special recognition or retroactive awards.")

    with st.form("manual_award_form"):
        # Get user list
        from app.services.roster_service import get_roster_service
        roster_service = get_roster_service()

        # For simplicity, ask for user email
        user_email = st.text_input(
            "Student Email",
            placeholder="student@example.com",
            help="Email of the student to award"
        )

        # Badge type
        award_type = st.selectbox(
            "Badge Type",
            options=["Skill", "Program"],
            help="Mini-badges should be awarded through the request approval process"
        )

        # Get badge based on type
        catalog_service = get_catalog_service()

        if award_type == "Skill":
            skills = catalog_service.list_skills(include_inactive=False)
            skill_options = {s.title: s.id for s in skills}

            selected_skill = st.selectbox(
                "Select Skill",
                options=list(skill_options.keys()) if skill_options else [],
                help="Select the skill to award"
            )
            badge_id = skill_options.get(selected_skill) if selected_skill else None

        else:  # Program
            programs = catalog_service.list_programs(include_inactive=False)
            program_options = {p.title: p.id for p in programs}

            selected_program = st.selectbox(
                "Select Program",
                options=list(program_options.keys()) if program_options else [],
                help="Select the program to award"
            )
            badge_id = program_options.get(selected_program) if selected_program else None

        # Reason
        reason = st.text_area(
            "Reason",
            placeholder="Special recognition, retroactive award, etc.",
            help="Why is this badge being manually awarded?"
        )

        submitted = st.form_submit_button("🏆 Award Badge")

        if submitted:
            # Validate inputs
            if not user_email:
                st.error("Please enter student email")
                return

            if not badge_id:
                st.error("Please select a badge")
                return

            if not reason or not reason.strip():
                st.error("Please provide a reason for the manual award")
                return

            # Get user
            user = roster_service.get_user_by_email(user_email)
            if not user:
                st.error(f"User not found: {user_email}")
                return

            # Award badge
            progress_service = get_progress_service()

            try:
                if award_type == "Skill":
                    award = progress_service.award_skill(
                        user_id=user.id,
                        skill_id=badge_id,
                        awarded_by=admin_user.id,
                        reason=reason.strip()
                    )
                else:  # Program
                    award = progress_service.award_program(
                        user_id=user.id,
                        program_id=badge_id,
                        awarded_by=admin_user.id,
                        reason=reason.strip()
                    )

                st.success(f"✅ {award_type} awarded to {user.username}!")
                st.balloons()

            except ProgressError as e:
                st.error(f"Failed to award badge: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")


def render_user_award_viewer() -> None:
    """Render viewer for individual user awards."""
    st.markdown("### 🔍 View User Awards")
    st.info("Search for a student to view their earned awards.")

    # Get user email
    from app.services.roster_service import get_roster_service
    roster_service = get_roster_service()

    user_email = st.text_input(
        "Student Email",
        placeholder="student@example.com",
        help="Email of the student to view"
    )

    if user_email:
        user = roster_service.get_user_by_email(user_email)

        if not user:
            st.warning(f"User not found: {user_email}")
            return

        st.markdown(f"### Awards for **{user.username}** ({user.email})")
        st.markdown("---")

        progress_service = get_progress_service()
        awards = progress_service.get_user_awards(user.id)

        if not awards:
            st.info(f"{user.username} hasn't earned any badges yet.")
            return

        # Organize by type
        mini_badges = [a for a in awards if a.award_type == AwardType.MINI_BADGE]
        skills = [a for a in awards if a.award_type == AwardType.SKILL]
        programs = [a for a in awards if a.award_type == AwardType.PROGRAM]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🏅 Mini-Badges", len(mini_badges))

        with col2:
            st.metric("⭐ Skills", len(skills))

        with col3:
            st.metric("🏆 Programs", len(programs))

        st.markdown("---")

        # List awards
        st.markdown("### All Awards")

        for award in sorted(awards, key=lambda a: a.awarded_at, reverse=True):
            render_award_badge(award)

            # Show notes if manual award
            if award.notes:
                st.caption(f"💬 Note: {award.notes}")

            st.markdown("---")
