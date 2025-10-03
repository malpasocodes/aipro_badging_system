"""Roster UI component for user management."""

import streamlit as st

from app.models.user import User, UserRole
from app.services.roster_service import (
    AuthorizationError,
    RosterError,
    get_roster_service,
)


def render_roster(user: User, can_edit_roles: bool = False) -> None:
    """
    Render the user roster for admins/assistants.

    Args:
        user: Current logged-in user
        can_edit_roles: Whether the user can edit roles (admin only)
    """
    st.markdown("### 👥 User Roster")

    roster_service = get_roster_service()

    # Get user statistics
    stats = roster_service.get_user_stats()

    # Show metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats["total"])
    with col2:
        st.metric("Students", stats["students"])
    with col3:
        st.metric("Assistants", stats["assistants"])
    with col4:
        st.metric("Admins", stats["admins"])

    # Role filter
    role_filter_option = st.selectbox(
        "Filter by role",
        ["All", "Students", "Assistants", "Admins"],
    )

    role_filter_map = {
        "All": None,
        "Students": UserRole.STUDENT,
        "Assistants": UserRole.ASSISTANT,
        "Admins": UserRole.ADMIN,
    }
    role_filter = role_filter_map[role_filter_option]

    # Get users
    users = roster_service.get_all_users(role_filter=role_filter, limit=1000)

    if not users:
        st.info("No users found matching the filter.")
        return

    st.markdown(f"**Showing {len(users)} user(s)**")
    st.markdown("---")

    # Render user table
    for roster_user in users:
        _render_user_row(roster_user, user, can_edit_roles)


def _render_user_row(roster_user: User, current_user: User, can_edit_roles: bool) -> None:
    """
    Render a single user row.

    Args:
        roster_user: User being displayed
        current_user: Current logged-in user
        can_edit_roles: Whether roles can be edited
    """
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            # Username and email
            display_name = roster_user.username if roster_user.username else roster_user.email
            st.markdown(f"**{display_name}**")
            if roster_user.username:
                st.caption(f"Email: {roster_user.email}")

        with col2:
            # Role badge
            role_emoji = {
                UserRole.ADMIN: "👑",
                UserRole.ASSISTANT: "🎯",
                UserRole.STUDENT: "🎓",
            }
            st.markdown(f"{role_emoji[roster_user.role]} **{roster_user.role.value.title()}**")

        with col3:
            # Onboarding status
            if roster_user.is_onboarded():
                st.markdown("✅ Onboarded")
            else:
                st.markdown("⚠️ Not Onboarded")

            # Last login
            if roster_user.last_login_at:
                st.caption(f"Last login: {roster_user.last_login_at.strftime('%Y-%m-%d')}")

        with col4:
            # Edit role button (admin only)
            if can_edit_roles and roster_user.id != current_user.id:
                if st.button(
                    "Edit Role",
                    key=f"edit_role_{roster_user.id}",
                    use_container_width=True,
                ):
                    st.session_state[f"edit_role_modal_{roster_user.id}"] = True
                    st.rerun()

                # Show edit role modal if triggered
                if st.session_state.get(f"edit_role_modal_{roster_user.id}", False):
                    _show_edit_role_modal(roster_user, current_user)

        st.markdown("---")


@st.dialog("Edit User Role")
def _show_edit_role_modal(roster_user: User, current_user: User) -> None:
    """
    Show modal dialog for editing a user's role.

    Args:
        roster_user: User whose role is being edited
        current_user: Current admin user making the change
    """
    st.markdown(f"**User:** {roster_user.username or roster_user.email}")
    st.markdown(f"**Current Role:** {roster_user.role.value.title()}")
    st.markdown("---")

    # Role selector
    new_role = st.selectbox(
        "New Role",
        [UserRole.STUDENT, UserRole.ASSISTANT, UserRole.ADMIN],
        format_func=lambda r: f"{r.value.title()}",
        index=[UserRole.STUDENT, UserRole.ASSISTANT, UserRole.ADMIN].index(roster_user.role),
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancel", use_container_width=True):
            # Clear modal state
            st.session_state[f"edit_role_modal_{roster_user.id}"] = False
            st.rerun()

    with col2:
        if st.button("Save Changes", type="primary", use_container_width=True):
            if new_role == roster_user.role:
                st.info("No changes made - role is the same")
                return

            try:
                roster_service = get_roster_service()
                roster_service.update_user_role(
                    user_id=roster_user.id,
                    new_role=new_role,
                    actor_id=current_user.id,
                    actor_role=current_user.role,
                )

                # Clear modal state
                st.session_state[f"edit_role_modal_{roster_user.id}"] = False

                st.success(
                    f"✅ Role updated from {roster_user.role.value} to {new_role.value}"
                )
                st.rerun()

            except AuthorizationError as e:
                st.error(f"❌ Authorization error: {str(e)}")
            except RosterError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                import logging
                logging.exception("Unexpected error during role update")
