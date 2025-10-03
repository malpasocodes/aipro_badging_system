"""Badge picker component for request forms."""

from uuid import UUID

import streamlit as st

from app.services import get_catalog_service


def render_badge_picker(key_prefix: str = "badge_picker") -> UUID | None:
    """
    Render hierarchical badge picker with cascading Program → Skill → MiniBadge selection.

    Args:
        key_prefix: Prefix for session state keys to avoid conflicts

    Returns:
        Selected mini_badge_id (UUID) or None if incomplete selection
    """
    catalog_service = get_catalog_service()

    # Get programs
    programs = catalog_service.list_programs(include_inactive=False)

    if not programs:
        st.warning("No active programs available. Contact an administrator.")
        return None

    # Step 1: Select Program
    selected_program_idx = st.selectbox(
        "1️⃣ Select Program",
        options=range(len(programs)),
        format_func=lambda i: programs[i].title,
        key=f"{key_prefix}_program",
        help="Choose the badge program you want to request from"
    )

    if selected_program_idx is None:
        return None

    selected_program = programs[selected_program_idx]

    # Step 2: Select Skill (filtered by program)
    skills = catalog_service.list_skills(program_id=selected_program.id, include_inactive=False)

    if not skills:
        st.info(f"No active skills in {selected_program.title}. Contact an administrator.")
        return None

    selected_skill_idx = st.selectbox(
        "2️⃣ Select Skill",
        options=range(len(skills)),
        format_func=lambda i: skills[i].title,
        key=f"{key_prefix}_skill",
        help=f"Choose a skill within {selected_program.title}"
    )

    if selected_skill_idx is None:
        return None

    selected_skill = skills[selected_skill_idx]

    # Step 3: Select Mini-badge (filtered by skill)
    mini_badges = catalog_service.list_mini_badges(skill_id=selected_skill.id, include_inactive=False)

    if not mini_badges:
        st.info(f"No active mini-badges in {selected_skill.title}. Contact an administrator.")
        return None

    selected_badge_idx = st.selectbox(
        "3️⃣ Select Mini-badge",
        options=range(len(mini_badges)),
        format_func=lambda i: mini_badges[i].title,
        key=f"{key_prefix}_mini_badge",
        help=f"Choose a mini-badge to request from {selected_skill.title}"
    )

    if selected_badge_idx is None:
        return None

    selected_badge = mini_badges[selected_badge_idx]

    # Show preview of selected badge
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 Selected Badge Preview")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Badge:** {selected_badge.title}")
            if selected_badge.description:
                st.caption(selected_badge.description)

        with col2:
            st.markdown(f"**Skill:** {selected_skill.title}")
            st.markdown(f"**Program:** {selected_program.title}")

    return selected_badge.id


def render_badge_picker_compact(key_prefix: str = "badge_picker_compact") -> dict | None:
    """
    Render compact badge picker that returns full badge context.

    Returns:
        Dict with mini_badge_id, title, skill_title, program_title or None
    """
    catalog_service = get_catalog_service()

    # Get programs
    programs = catalog_service.list_programs(include_inactive=False)

    if not programs:
        st.error("⚠️ No badges available")
        return None

    # Single dropdown with flattened hierarchy
    badge_options = []
    badge_map = {}

    for program in programs:
        skills = catalog_service.list_skills(program_id=program.id, include_inactive=False)
        for skill in skills:
            mini_badges = catalog_service.list_mini_badges(skill_id=skill.id, include_inactive=False)
            for badge in mini_badges:
                option_text = f"{program.title} → {skill.title} → {badge.title}"
                badge_options.append(option_text)
                badge_map[option_text] = {
                    "mini_badge_id": badge.id,
                    "title": badge.title,
                    "description": badge.description,
                    "skill_title": skill.title,
                    "program_title": program.title,
                }

    if not badge_options:
        st.info("No badges available yet")
        return None

    # Single selectbox with all badges
    selected_option = st.selectbox(
        "Select Badge",
        options=badge_options,
        key=f"{key_prefix}_select",
        help="Program → Skill → Badge"
    )

    if selected_option:
        selected_badge = badge_map[selected_option]

        # Show preview
        with st.expander("📋 Badge Details", expanded=False):
            st.markdown(f"**{selected_badge['title']}**")
            if selected_badge["description"]:
                st.caption(selected_badge["description"])
            st.markdown(f"**Skill:** {selected_badge['skill_title']}")
            st.markdown(f"**Program:** {selected_badge['program_title']}")

        return selected_badge

    return None
