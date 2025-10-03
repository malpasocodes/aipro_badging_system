"""Reusable badge display components for progress tracking."""

from datetime import datetime
from typing import Any

import streamlit as st

from app.models.award import Award, AwardType


def render_badge_card(
    title: str,
    badge_type: str,
    earned: bool = False,
    earned_date: datetime | None = None,
    progress_percent: int | None = None,
    description: str | None = None,
) -> None:
    """
    Render a single badge card with status and progress.

    Args:
        title: Badge title
        badge_type: Type of badge (mini_badge, skill, program)
        earned: Whether the badge is earned
        earned_date: Date earned (if earned)
        progress_percent: Progress percentage (if in progress)
        description: Optional badge description
    """
    # Choose emoji based on badge type
    type_emoji = {
        "mini_badge": "🏅",
        "skill": "⭐",
        "program": "🏆",
    }
    emoji = type_emoji.get(badge_type, "🎖️")

    # Status indicator
    if earned:
        status = "✅ Earned"
        status_color = "green"
    elif progress_percent is not None and progress_percent > 0:
        status = f"🔄 {progress_percent}% Complete"
        status_color = "blue"
    else:
        status = "⏳ Not Started"
        status_color = "gray"

    # Render card
    with st.container():
        # Header with emoji and title
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {emoji} {title}")
        with col2:
            if status_color == "green":
                st.success(status)
            elif status_color == "blue":
                st.info(status)
            else:
                st.caption(status)

        # Description
        if description:
            st.caption(description)

        # Progress bar
        if not earned and progress_percent is not None:
            st.progress(progress_percent / 100.0)

        # Earned date
        if earned and earned_date:
            st.caption(f"Earned: {earned_date.strftime('%B %d, %Y')}")

        st.markdown("---")


def render_mini_badge_list(
    mini_badges: list[dict[str, Any]],
    show_progress: bool = True
) -> None:
    """
    Render a list of mini-badges with earned status.

    Args:
        mini_badges: List of mini-badge data dicts with keys:
            - id, title, description, is_active, earned, earned_date
        show_progress: Whether to show progress indicators
    """
    if not mini_badges:
        st.info("No mini-badges available")
        return

    earned_count = sum(1 for mb in mini_badges if mb.get("earned"))
    total_count = len(mini_badges)

    if show_progress:
        st.markdown(f"**Progress:** {earned_count} of {total_count} earned")
        st.progress(earned_count / total_count if total_count > 0 else 0)
        st.markdown("---")

    for mb in mini_badges:
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            if mb.get("earned"):
                st.markdown("✅")
            else:
                st.markdown("⏳")

        with col2:
            st.markdown(f"**{mb['title']}**")
            if mb.get("description"):
                st.caption(mb["description"])

        with col3:
            if mb.get("earned") and mb.get("earned_date"):
                st.caption(mb["earned_date"].strftime("%m/%d/%y"))


def render_skill_card(
    skill_title: str,
    earned: bool,
    progress_percent: int,
    mini_badge_count: int,
    earned_date: datetime | None = None,
) -> None:
    """
    Render a skill card with mini-badge progress.

    Args:
        skill_title: Skill title
        earned: Whether skill is earned
        progress_percent: Progress percentage toward skill
        mini_badge_count: Number of mini-badges in skill
        earned_date: Date earned (if earned)
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### ⭐ {skill_title}")

        with col2:
            if earned:
                st.success("✅ Earned")
            else:
                st.info(f"{progress_percent}%")

        # Progress bar
        if not earned:
            st.progress(progress_percent / 100.0)
            st.caption(f"{mini_badge_count} mini-badges")

        # Earned date
        if earned and earned_date:
            st.caption(f"Earned: {earned_date.strftime('%B %d, %Y')}")

        st.markdown("---")


def render_program_card(
    program_title: str,
    description: str | None,
    earned: bool,
    progress_percent: int,
    skill_count: int,
    earned_skills: int,
    earned_date: datetime | None = None,
) -> None:
    """
    Render a program card with skill progress.

    Args:
        program_title: Program title
        description: Program description
        earned: Whether program is earned
        progress_percent: Progress percentage toward program
        skill_count: Total number of skills in program
        earned_skills: Number of skills earned
        earned_date: Date earned (if earned)
    """
    with st.container():
        # Header
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"## 🏆 {program_title}")

        with col2:
            if earned:
                st.success("✅ Complete")
            else:
                st.info(f"{progress_percent}%")

        # Description
        if description:
            st.caption(description)

        # Progress
        if not earned:
            st.progress(progress_percent / 100.0)
            st.caption(f"Skills: {earned_skills} of {skill_count} complete")

        # Earned date
        if earned and earned_date:
            st.success(f"🎉 Program completed on {earned_date.strftime('%B %d, %Y')}")

        st.markdown("---")


def render_award_badge(award: Award) -> None:
    """
    Render a single award with details.

    Args:
        award: Award object to display
    """
    # Determine badge type and emoji
    type_emoji = {
        AwardType.MINI_BADGE: "🏅",
        AwardType.SKILL: "⭐",
        AwardType.PROGRAM: "🏆",
    }
    emoji = type_emoji.get(award.award_type, "🎖️")

    # Get badge title based on type
    badge_id = award.get_badge_id()
    badge_title = f"{award.award_type.value.replace('_', ' ').title()}"

    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])

        with col1:
            st.markdown(f"## {emoji}")

        with col2:
            st.markdown(f"**{badge_title}**")
            st.caption(f"ID: {str(badge_id)[:8]}...")

        with col3:
            st.caption(f"Earned: {award.awarded_at.strftime('%m/%d/%Y')}")
            if award.is_automatic():
                st.caption("🤖 Automatic")
            else:
                st.caption("👤 Manual")


def render_progress_summary(
    total_mini_badges: int,
    earned_mini_badges: int,
    total_skills: int,
    earned_skills: int,
    total_programs: int,
    earned_programs: int,
) -> None:
    """
    Render overall progress summary metrics.

    Args:
        total_mini_badges: Total available mini-badges
        earned_mini_badges: Mini-badges earned
        total_skills: Total available skills
        earned_skills: Skills earned
        total_programs: Total available programs
        earned_programs: Programs earned
    """
    st.markdown("### 📊 Overall Progress")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🏅 Mini-Badges",
            f"{earned_mini_badges}/{total_mini_badges}",
            delta=None,
            help="Individual badges earned"
        )
        if total_mini_badges > 0:
            percent = int((earned_mini_badges / total_mini_badges) * 100)
            st.progress(percent / 100.0)

    with col2:
        st.metric(
            "⭐ Skills",
            f"{earned_skills}/{total_skills}",
            delta=None,
            help="Skills mastered"
        )
        if total_skills > 0:
            percent = int((earned_skills / total_skills) * 100)
            st.progress(percent / 100.0)

    with col3:
        st.metric(
            "🏆 Programs",
            f"{earned_programs}/{total_programs}",
            delta=None,
            help="Programs completed"
        )
        if total_programs > 0:
            percent = int((earned_programs / total_programs) * 100)
            st.progress(percent / 100.0)

    st.markdown("---")
