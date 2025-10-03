"""Admin catalog management UI for badge hierarchy."""


import streamlit as st

from app.models import Capstone, MiniBadge, Program, Skill, User
from app.services import get_catalog_service


def render_catalog_management(user: User) -> None:
    """Render admin catalog management interface."""
    if not user.is_admin():
        st.error("🔐 Access denied. Admins only.")
        return

    st.markdown("## 📚 Badge Catalog Management")
    st.markdown("Manage programs, skills, mini-badges, and capstones.")

    # Create tabs for each entity type
    tabs = st.tabs(["📖 Programs", "🎯 Skills", "🏅 Mini-badges", "🎓 Capstones"])

    with tabs[0]:
        render_programs_tab(user)

    with tabs[1]:
        render_skills_tab(user)

    with tabs[2]:
        render_mini_badges_tab(user)

    with tabs[3]:
        render_capstones_tab(user)


# ==================== PROGRAMS TAB ====================

def render_programs_tab(user: User) -> None:
    """Render programs management tab."""
    st.markdown("### Programs")

    catalog_service = get_catalog_service()

    # Add new program button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Program", key="add_program_btn", use_container_width=True):
            st.session_state["show_add_program_modal"] = True

    # Show add program modal
    if st.session_state.get("show_add_program_modal"):
        show_add_program_modal(user)

    # List programs
    programs = catalog_service.list_programs(include_inactive=True)

    if not programs:
        st.info("No programs yet. Click 'Add Program' to create one.")
        return

    # Display programs in a table-like format
    for program in programs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

            with col1:
                status_icon = "✅" if program.is_active else "⏸️"
                st.markdown(f"**{status_icon} {program.title}**")
                if program.description:
                    st.caption(program.description[:100] + "..." if len(program.description) > 100 else program.description)

            with col2:
                # Count children
                skills = catalog_service.list_skills(program_id=program.id, include_inactive=True)
                st.caption(f"📊 {len(skills)} skills")

            with col3:
                # Toggle active/inactive
                if program.is_active:
                    if st.button("Deactivate", key=f"deactivate_prog_{program.id}", use_container_width=True):
                        try:
                            catalog_service.toggle_program_active(program.id, False, user.id, user.role)
                            st.success(f"Deactivated: {program.title}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    if st.button("Activate", key=f"activate_prog_{program.id}", use_container_width=True):
                        try:
                            catalog_service.toggle_program_active(program.id, True, user.id, user.role)
                            st.success(f"Activated: {program.title}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col4:
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    if st.button("✏️ Edit", key=f"edit_prog_{program.id}", use_container_width=True):
                        st.session_state[f"edit_program_{program.id}"] = True
                        st.rerun()
                with subcol2:
                    if st.button("🗑️ Delete", key=f"delete_prog_{program.id}", use_container_width=True):
                        st.session_state[f"delete_program_{program.id}"] = True
                        st.rerun()

            st.divider()

        # Show edit modal
        if st.session_state.get(f"edit_program_{program.id}"):
            show_edit_program_modal(user, program)

        # Show delete confirmation
        if st.session_state.get(f"delete_program_{program.id}"):
            show_delete_program_modal(user, program)


@st.dialog("Add New Program")
def show_add_program_modal(user: User) -> None:
    """Modal for adding new program."""
    catalog_service = get_catalog_service()

    title = st.text_input("Program Title *", max_chars=200, key="new_program_title")
    description = st.text_area("Description", key="new_program_description")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if not title:
                st.error("Title is required")
                return

            try:
                program = catalog_service.create_program(
                    title=title,
                    description=description if description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Created: {program.title}")
                st.session_state["show_add_program_modal"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_add_program_modal"] = False
            st.rerun()


@st.dialog("Edit Program")
def show_edit_program_modal(user: User, program: Program) -> None:
    """Modal for editing program."""
    catalog_service = get_catalog_service()

    title = st.text_input("Program Title *", value=program.title, max_chars=200, key=f"edit_title_{program.id}")
    description = st.text_area("Description", value=program.description or "", key=f"edit_desc_{program.id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            try:
                updated = catalog_service.update_program(
                    program_id=program.id,
                    title=title if title != program.title else None,
                    description=description if description != program.description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Updated: {updated.title}")
                st.session_state[f"edit_program_{program.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"edit_program_{program.id}"] = False
            st.rerun()


@st.dialog("Delete Program?")
def show_delete_program_modal(user: User, program: Program) -> None:
    """Modal for deleting program."""
    catalog_service = get_catalog_service()

    # Check dependencies
    skills = catalog_service.list_skills(program_id=program.id, include_inactive=True)
    capstones = catalog_service.list_capstones(program_id=program.id, include_inactive=True)

    if skills or capstones:
        st.warning(f"⚠️ This program has {len(skills)} skills and {len(capstones)} capstones.")
        st.markdown("**Delete all children first, or deactivate instead.**")

        if st.button("Close", use_container_width=True):
            st.session_state[f"delete_program_{program.id}"] = False
            st.rerun()
    else:
        st.warning(f"⚠️ Delete **{program.title}**? This cannot be undone.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete", type="primary", use_container_width=True):
                try:
                    catalog_service.delete_program(program.id, user.id, user.role)
                    st.success(f"🗑️ Deleted: {program.title}")
                    st.session_state[f"delete_program_{program.id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state[f"delete_program_{program.id}"] = False
                st.rerun()


# ==================== SKILLS TAB ====================

def render_skills_tab(user: User) -> None:
    """Render skills management tab."""
    st.markdown("### Skills")

    catalog_service = get_catalog_service()
    programs = catalog_service.list_programs(include_inactive=True)

    if not programs:
        st.info("Create a program first before adding skills.")
        return

    # Filter by program
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_program = st.selectbox(
            "Filter by Program",
            options=[None] + programs,
            format_func=lambda p: "All Programs" if p is None else f"{p.title} {'(inactive)' if not p.is_active else ''}",
            key="skills_program_filter"
        )
    with col2:
        if st.button("➕ Add Skill", key="add_skill_btn", use_container_width=True):
            st.session_state["show_add_skill_modal"] = True

    # Show add skill modal
    if st.session_state.get("show_add_skill_modal"):
        show_add_skill_modal(user, programs)

    # List skills
    program_id = selected_program.id if selected_program else None
    skills = catalog_service.list_skills(program_id=program_id, include_inactive=True)

    if not skills:
        st.info("No skills yet. Click 'Add Skill' to create one.")
        return

    # Display skills
    for skill in skills:
        program = catalog_service.get_program(skill.program_id)

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

            with col1:
                status_icon = "✅" if skill.is_active else "⏸️"
                st.markdown(f"**{status_icon} {skill.title}**")
                st.caption(f"Program: {program.title if program else 'Unknown'}")

            with col2:
                # Count mini-badges
                mini_badges = catalog_service.list_mini_badges(skill_id=skill.id, include_inactive=True)
                st.caption(f"🏅 {len(mini_badges)} badges")

            with col3:
                # Toggle active/inactive
                if skill.is_active:
                    if st.button("Deactivate", key=f"deactivate_skill_{skill.id}", use_container_width=True):
                        catalog_service.toggle_skill_active(skill.id, False, user.id, user.role)
                        st.rerun()
                else:
                    if st.button("Activate", key=f"activate_skill_{skill.id}", use_container_width=True):
                        catalog_service.toggle_skill_active(skill.id, True, user.id, user.role)
                        st.rerun()

            with col4:
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    if st.button("✏️ Edit", key=f"edit_skill_{skill.id}", use_container_width=True):
                        st.session_state[f"edit_skill_{skill.id}"] = True
                        st.rerun()
                with subcol2:
                    if st.button("🗑️ Delete", key=f"delete_skill_{skill.id}", use_container_width=True):
                        st.session_state[f"delete_skill_{skill.id}"] = True
                        st.rerun()

            st.divider()

        # Show edit modal
        if st.session_state.get(f"edit_skill_{skill.id}"):
            show_edit_skill_modal(user, skill, programs)

        # Show delete modal
        if st.session_state.get(f"delete_skill_{skill.id}"):
            show_delete_skill_modal(user, skill)


@st.dialog("Add New Skill")
def show_add_skill_modal(user: User, programs: list[Program]) -> None:
    """Modal for adding new skill."""
    catalog_service = get_catalog_service()

    # Select program
    active_programs = [p for p in programs if p.is_active]
    if not active_programs:
        st.error("No active programs available. Activate a program first.")
        return

    program = st.selectbox(
        "Program *",
        options=active_programs,
        format_func=lambda p: p.title,
        key="new_skill_program"
    )

    title = st.text_input("Skill Title *", max_chars=200, key="new_skill_title")
    description = st.text_area("Description", key="new_skill_description")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if not title:
                st.error("Title is required")
                return
            if not program:
                st.error("Program is required")
                return

            try:
                skill = catalog_service.create_skill(
                    program_id=program.id,
                    title=title,
                    description=description if description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Created: {skill.title}")
                st.session_state["show_add_skill_modal"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_add_skill_modal"] = False
            st.rerun()


@st.dialog("Edit Skill")
def show_edit_skill_modal(user: User, skill: Skill, programs: list[Program]) -> None:
    """Modal for editing skill."""
    catalog_service = get_catalog_service()

    title = st.text_input("Skill Title *", value=skill.title, max_chars=200, key=f"edit_skill_title_{skill.id}")
    description = st.text_area("Description", value=skill.description or "", key=f"edit_skill_desc_{skill.id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            try:
                catalog_service.update_skill(
                    skill_id=skill.id,
                    title=title if title != skill.title else None,
                    description=description if description != skill.description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Updated: {title}")
                st.session_state[f"edit_skill_{skill.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"edit_skill_{skill.id}"] = False
            st.rerun()


@st.dialog("Delete Skill?")
def show_delete_skill_modal(user: User, skill: Skill) -> None:
    """Modal for deleting skill."""
    catalog_service = get_catalog_service()

    # Check dependencies
    mini_badges = catalog_service.list_mini_badges(skill_id=skill.id, include_inactive=True)

    if mini_badges:
        st.warning(f"⚠️ This skill has {len(mini_badges)} mini-badges.")
        st.markdown("**Delete all mini-badges first, or deactivate instead.**")

        if st.button("Close", use_container_width=True):
            st.session_state[f"delete_skill_{skill.id}"] = False
            st.rerun()
    else:
        st.warning(f"⚠️ Delete **{skill.title}**? This cannot be undone.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete", type="primary", use_container_width=True):
                try:
                    catalog_service.delete_skill(skill.id, user.id, user.role)
                    st.success(f"🗑️ Deleted: {skill.title}")
                    st.session_state[f"delete_skill_{skill.id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state[f"delete_skill_{skill.id}"] = False
                st.rerun()


# ==================== MINI-BADGES TAB ====================

def render_mini_badges_tab(user: User) -> None:
    """Render mini-badges management tab."""
    st.markdown("### Mini-badges")

    catalog_service = get_catalog_service()
    programs = catalog_service.list_programs(include_inactive=True)

    if not programs:
        st.info("Create a program and skill first before adding mini-badges.")
        return

    # Cascading filter: Program → Skill
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        selected_program = st.selectbox(
            "Filter by Program",
            options=[None] + programs,
            format_func=lambda p: "All Programs" if p is None else p.title,
            key="mini_badges_program_filter"
        )

    with col2:
        if selected_program:
            skills = catalog_service.list_skills(program_id=selected_program.id, include_inactive=True)
            selected_skill = st.selectbox(
                "Filter by Skill",
                options=[None] + skills,
                format_func=lambda s: "All Skills" if s is None else s.title,
                key="mini_badges_skill_filter"
            )
        else:
            selected_skill = None
            st.selectbox("Filter by Skill", options=["Select program first"], disabled=True)

    with col3:
        if st.button("➕ Add Badge", key="add_mini_badge_btn", use_container_width=True):
            st.session_state["show_add_mini_badge_modal"] = True

    # Show add mini-badge modal
    if st.session_state.get("show_add_mini_badge_modal"):
        show_add_mini_badge_modal(user, programs)

    # List mini-badges
    skill_id = selected_skill.id if selected_skill else None
    mini_badges = catalog_service.list_mini_badges(skill_id=skill_id, include_inactive=True)

    if not mini_badges:
        st.info("No mini-badges yet. Click 'Add Badge' to create one.")
        return

    # Display mini-badges
    for badge in mini_badges:
        skill = catalog_service.get_skill(badge.skill_id)
        program = catalog_service.get_program(skill.program_id) if skill else None

        with st.container():
            col1, col2, col3 = st.columns([4, 1, 2])

            with col1:
                status_icon = "✅" if badge.is_active else "⏸️"
                st.markdown(f"**{status_icon} {badge.title}**")
                st.caption(f"Skill: {skill.title if skill else 'Unknown'} | Program: {program.title if program else 'Unknown'}")

            with col2:
                # Toggle active/inactive
                if badge.is_active:
                    if st.button("Deactivate", key=f"deactivate_badge_{badge.id}", use_container_width=True):
                        catalog_service.toggle_mini_badge_active(badge.id, False, user.id, user.role)
                        st.rerun()
                else:
                    if st.button("Activate", key=f"activate_badge_{badge.id}", use_container_width=True):
                        catalog_service.toggle_mini_badge_active(badge.id, True, user.id, user.role)
                        st.rerun()

            with col3:
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    if st.button("✏️ Edit", key=f"edit_badge_{badge.id}", use_container_width=True):
                        st.session_state[f"edit_badge_{badge.id}"] = True
                        st.rerun()
                with subcol2:
                    if st.button("🗑️ Delete", key=f"delete_badge_{badge.id}", use_container_width=True):
                        st.session_state[f"delete_badge_{badge.id}"] = True
                        st.rerun()

            st.divider()

        # Show edit modal
        if st.session_state.get(f"edit_badge_{badge.id}"):
            show_edit_mini_badge_modal(user, badge)

        # Show delete modal
        if st.session_state.get(f"delete_badge_{badge.id}"):
            show_delete_mini_badge_modal(user, badge)


@st.dialog("Add New Mini-badge")
def show_add_mini_badge_modal(user: User, programs: list[Program]) -> None:
    """Modal for adding new mini-badge."""
    catalog_service = get_catalog_service()

    # Select program, then skill (cascading)
    active_programs = [p for p in programs if p.is_active]
    if not active_programs:
        st.error("No active programs available.")
        return

    program = st.selectbox(
        "Program *",
        options=active_programs,
        format_func=lambda p: p.title,
        key="new_badge_program"
    )

    if program:
        skills = catalog_service.list_skills(program_id=program.id, include_inactive=False)
        if not skills:
            st.error(f"No active skills in {program.title}. Create a skill first.")
            return

        skill = st.selectbox(
            "Skill *",
            options=skills,
            format_func=lambda s: s.title,
            key="new_badge_skill"
        )
    else:
        skill = None
        st.selectbox("Skill *", options=["Select program first"], disabled=True)

    title = st.text_input("Mini-badge Title *", max_chars=200, key="new_badge_title")
    description = st.text_area("Description", key="new_badge_description")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if not title:
                st.error("Title is required")
                return
            if not skill:
                st.error("Skill is required")
                return

            try:
                badge = catalog_service.create_mini_badge(
                    skill_id=skill.id,
                    title=title,
                    description=description if description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Created: {badge.title}")
                st.session_state["show_add_mini_badge_modal"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_add_mini_badge_modal"] = False
            st.rerun()


@st.dialog("Edit Mini-badge")
def show_edit_mini_badge_modal(user: User, badge: MiniBadge) -> None:
    """Modal for editing mini-badge."""
    catalog_service = get_catalog_service()

    title = st.text_input("Title *", value=badge.title, max_chars=200, key=f"edit_badge_title_{badge.id}")
    description = st.text_area("Description", value=badge.description or "", key=f"edit_badge_desc_{badge.id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            try:
                catalog_service.update_mini_badge(
                    mini_badge_id=badge.id,
                    title=title if title != badge.title else None,
                    description=description if description != badge.description else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Updated: {title}")
                st.session_state[f"edit_badge_{badge.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"edit_badge_{badge.id}"] = False
            st.rerun()


@st.dialog("Delete Mini-badge?")
def show_delete_mini_badge_modal(user: User, badge: MiniBadge) -> None:
    """Modal for deleting mini-badge."""
    catalog_service = get_catalog_service()

    st.warning(f"⚠️ Delete **{badge.title}**? This cannot be undone.")
    st.caption("Note: Cannot delete if any requests reference this badge.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete", type="primary", use_container_width=True):
            try:
                catalog_service.delete_mini_badge(badge.id, user.id, user.role)
                st.success(f"🗑️ Deleted: {badge.title}")
                st.session_state[f"delete_badge_{badge.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"delete_badge_{badge.id}"] = False
            st.rerun()


# ==================== CAPSTONES TAB ====================

def render_capstones_tab(user: User) -> None:
    """Render capstones management tab."""
    st.markdown("### Capstones")

    catalog_service = get_catalog_service()
    programs = catalog_service.list_programs(include_inactive=True)

    if not programs:
        st.info("Create a program first before adding capstones.")
        return

    # Filter by program
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_program = st.selectbox(
            "Filter by Program",
            options=[None] + programs,
            format_func=lambda p: "All Programs" if p is None else p.title,
            key="capstones_program_filter"
        )
    with col2:
        if st.button("➕ Add Capstone", key="add_capstone_btn", use_container_width=True):
            st.session_state["show_add_capstone_modal"] = True

    # Show add capstone modal
    if st.session_state.get("show_add_capstone_modal"):
        show_add_capstone_modal(user, programs)

    # List capstones
    program_id = selected_program.id if selected_program else None
    capstones = catalog_service.list_capstones(program_id=program_id, include_inactive=True)

    if not capstones:
        st.info("No capstones yet. Click 'Add Capstone' to create one.")
        return

    # Display capstones
    for capstone in capstones:
        program = catalog_service.get_program(capstone.program_id)

        with st.container():
            col1, col2, col3 = st.columns([4, 1, 2])

            with col1:
                status_icon = "✅" if capstone.is_active else "⏸️"
                required_icon = "⭐" if capstone.is_required else "💫"
                st.markdown(f"**{status_icon} {required_icon} {capstone.title}**")
                st.caption(f"Program: {program.title if program else 'Unknown'} | {'Required' if capstone.is_required else 'Optional'}")

            with col2:
                # Toggle active/inactive
                if capstone.is_active:
                    if st.button("Deactivate", key=f"deactivate_capstone_{capstone.id}", use_container_width=True):
                        catalog_service.toggle_capstone_active(capstone.id, False, user.id, user.role)
                        st.rerun()
                else:
                    if st.button("Activate", key=f"activate_capstone_{capstone.id}", use_container_width=True):
                        catalog_service.toggle_capstone_active(capstone.id, True, user.id, user.role)
                        st.rerun()

            with col3:
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    if st.button("✏️ Edit", key=f"edit_capstone_{capstone.id}", use_container_width=True):
                        st.session_state[f"edit_capstone_{capstone.id}"] = True
                        st.rerun()
                with subcol2:
                    if st.button("🗑️ Delete", key=f"delete_capstone_{capstone.id}", use_container_width=True):
                        st.session_state[f"delete_capstone_{capstone.id}"] = True
                        st.rerun()

            st.divider()

        # Show edit modal
        if st.session_state.get(f"edit_capstone_{capstone.id}"):
            show_edit_capstone_modal(user, capstone)

        # Show delete modal
        if st.session_state.get(f"delete_capstone_{capstone.id}"):
            show_delete_capstone_modal(user, capstone)


@st.dialog("Add New Capstone")
def show_add_capstone_modal(user: User, programs: list[Program]) -> None:
    """Modal for adding new capstone."""
    catalog_service = get_catalog_service()

    active_programs = [p for p in programs if p.is_active]
    if not active_programs:
        st.error("No active programs available.")
        return

    program = st.selectbox(
        "Program *",
        options=active_programs,
        format_func=lambda p: p.title,
        key="new_capstone_program"
    )

    title = st.text_input("Capstone Title *", max_chars=200, key="new_capstone_title")
    description = st.text_area("Description", key="new_capstone_description")
    is_required = st.checkbox("Required for program completion", key="new_capstone_required")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if not title:
                st.error("Title is required")
                return
            if not program:
                st.error("Program is required")
                return

            try:
                capstone = catalog_service.create_capstone(
                    program_id=program.id,
                    title=title,
                    description=description if description else None,
                    is_required=is_required,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Created: {capstone.title}")
                st.session_state["show_add_capstone_modal"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_add_capstone_modal"] = False
            st.rerun()


@st.dialog("Edit Capstone")
def show_edit_capstone_modal(user: User, capstone: Capstone) -> None:
    """Modal for editing capstone."""
    catalog_service = get_catalog_service()

    title = st.text_input("Title *", value=capstone.title, max_chars=200, key=f"edit_capstone_title_{capstone.id}")
    description = st.text_area("Description", value=capstone.description or "", key=f"edit_capstone_desc_{capstone.id}")
    is_required = st.checkbox("Required for program completion", value=capstone.is_required, key=f"edit_capstone_req_{capstone.id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            try:
                catalog_service.update_capstone(
                    capstone_id=capstone.id,
                    title=title if title != capstone.title else None,
                    description=description if description != capstone.description else None,
                    is_required=is_required if is_required != capstone.is_required else None,
                    actor_id=user.id,
                    actor_role=user.role,
                )
                st.success(f"✅ Updated: {title}")
                st.session_state[f"edit_capstone_{capstone.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"edit_capstone_{capstone.id}"] = False
            st.rerun()


@st.dialog("Delete Capstone?")
def show_delete_capstone_modal(user: User, capstone: Capstone) -> None:
    """Modal for deleting capstone."""
    catalog_service = get_catalog_service()

    st.warning(f"⚠️ Delete **{capstone.title}**? This cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete", type="primary", use_container_width=True):
            try:
                catalog_service.delete_capstone(capstone.id, user.id, user.role)
                st.success(f"🗑️ Deleted: {capstone.title}")
                st.session_state[f"delete_capstone_{capstone.id}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"delete_capstone_{capstone.id}"] = False
            st.rerun()
