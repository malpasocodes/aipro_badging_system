"""User management UI components for admin functions."""

import streamlit as st

from app.models.user import User, UserRole
from app.services.roster_service import (
    AuthorizationError,
    RosterError,
    get_roster_service,
)


def render_user_roster(_user: User) -> None:
    """
    Render read-only user roster (no editing capabilities).

    Shows simple list of users with their role and onboarding status.

    Args:
        _user: Current admin user (not used, kept for consistency)
    """
    st.markdown("### 📊 User Roster")
    st.markdown("View all users in the system.")
    st.markdown("---")

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

    st.markdown("---")

    # Role filter
    role_filter_option = st.selectbox(
        "Filter by role",
        ["All", "Students", "Assistants", "Admins"],
        key="user_roster_filter",
    )

    role_filter_map = {
        "All": None,
        "Students": UserRole.STUDENT,
        "Assistants": UserRole.ASSISTANT,
        "Admins": UserRole.ADMIN,
    }
    role_filter = role_filter_map[role_filter_option]

    # Get users (exclude inactive/deleted users by default)
    users = roster_service.get_all_users(
        role_filter=role_filter, include_inactive=False, limit=1000
    )

    if not users:
        st.info("No users found matching the filter.")
        return

    st.markdown(f"**Showing {len(users)} user(s)**")
    st.markdown("---")

    # Render user table (read-only)
    for roster_user in users:
        _render_user_row_readonly(roster_user)


def _render_user_row_readonly(roster_user: User) -> None:
    """
    Render a single user row (read-only, no edit buttons).

    Args:
        roster_user: User being displayed
    """
    with st.container():
        col1, col2, col3 = st.columns([4, 2, 2])

        with col1:
            # Username and email
            display_name = (
                roster_user.username if roster_user.username else roster_user.email
            )
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
            st.markdown(
                f"{role_emoji[roster_user.role]} **{roster_user.role.value.title()}**"
            )

        with col3:
            # Status
            if not roster_user.is_active:
                st.markdown("🚫 Inactive")
            elif roster_user.is_onboarded():
                st.markdown("✅ Onboarded")
            else:
                st.markdown("⚠️ Not Onboarded")

            # Last login
            if roster_user.last_login_at:
                st.caption(
                    f"Last login: {roster_user.last_login_at.strftime('%Y-%m-%d')}"
                )

        st.markdown("---")


def render_add_delete_user(user: User) -> None:
    """
    Render add/delete user interface.

    Args:
        user: Current admin user
    """
    st.markdown("### ➕➖ Add / Delete User")
    st.markdown("Add new users or remove existing users from the system.")
    st.markdown("---")

    # Tabs for Add and Delete functions
    tab1, tab2 = st.tabs(["➕ Add User", "➖ Delete User"])

    with tab1:
        _render_add_user_form(user)

    with tab2:
        _render_delete_user_form(user)


def _render_add_user_form(admin_user: User) -> None:
    """
    Render form to add a new user.

    Args:
        admin_user: Current admin user
    """
    st.markdown("#### Add New User")
    st.info(
        "New users are created with **Student** role by default. "
        "They will complete onboarding on their first login."
    )

    with st.form("add_user_form"):
        email = st.text_input(
            "Email Address *",
            placeholder="user@example.com",
            help="User's email address (must be valid Google account)",
        )

        submitted = st.form_submit_button("➕ Add User", type="primary")

        if submitted:
            if not email or not email.strip():
                st.error("❌ Email address is required")
                return

            email = email.strip().lower()

            # Basic email validation
            if "@" not in email or "." not in email:
                st.error("❌ Invalid email address format")
                return

            try:
                roster_service = get_roster_service()

                # Check if user already exists
                existing_user = roster_service.get_user_by_email(email)
                if existing_user:
                    if existing_user.is_active:
                        st.error(f"❌ User with email {email} already exists")
                    else:
                        st.error(
                            f"❌ User with email {email} exists but is inactive. "
                            "Contact system administrator to reactivate."
                        )
                    return

                # Create new user
                new_user = roster_service.create_user(
                    email=email,
                    actor_id=admin_user.id,
                    actor_role=admin_user.role,
                )

                st.success(
                    f"✅ User created successfully: {new_user.email}\n\n"
                    f"Role: {new_user.role.value.title()}\n\n"
                    "They will complete onboarding on their first login."
                )

            except AuthorizationError as e:
                st.error(f"❌ Authorization error: {str(e)}")
            except RosterError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                import logging

                logging.exception("Unexpected error during user creation")


def _render_delete_user_form(admin_user: User) -> None:
    """
    Render form to delete a user.

    Args:
        admin_user: Current admin user
    """
    st.markdown("#### Delete User")
    st.warning(
        "⚠️ **Warning:** Deleting a user will deactivate their account. "
        "This is a soft delete - user data is preserved but they cannot log in."
    )

    roster_service = get_roster_service()

    # Get all active users except current admin
    all_users = roster_service.get_all_users(include_inactive=False, limit=1000)
    deletable_users = [u for u in all_users if u.id != admin_user.id]

    if not deletable_users:
        st.info("No users available to delete.")
        return

    # Use form to prevent reruns on selection/checkbox changes
    with st.form("delete_user_form"):
        # User selection
        user_options = {
            f"{u.username or u.email} ({u.email}) - {u.role.value.title()}": u
            for u in deletable_users
        }

        selected_user_key = st.selectbox(
            "Select user to delete",
            options=list(user_options.keys()),
            key="delete_user_select_form",
        )

        selected_user = user_options[selected_user_key]

        # Show user details
        st.markdown("---")
        st.markdown("**User Details:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Email:** {selected_user.email}")
        with col2:
            st.write(f"**Role:** {selected_user.role.value.title()}")
        with col3:
            status = "Onboarded" if selected_user.is_onboarded() else "Not Onboarded"
            st.write(f"**Status:** {status}")

        st.markdown("---")

        # Confirmation checkbox
        confirm = st.checkbox(
            f"I confirm I want to delete user: {selected_user.email}",
            key="delete_user_confirm_form",
        )

        # Submit button (always enabled - validation happens on submit)
        submitted = st.form_submit_button("🗑️ Delete User", type="primary")

        if submitted:
            # Validate confirmation
            if not confirm:
                st.error("❌ Please check the confirmation box to delete the user.")
                return

            try:
                deleted_user = roster_service.delete_user(
                    user_id=selected_user.id,
                    actor_id=admin_user.id,
                    actor_role=admin_user.role,
                )

                st.success(
                    f"✅ User deleted successfully: {deleted_user.email}\n\n"
                    "The user account has been deactivated."
                )
                st.rerun()

            except AuthorizationError as e:
                st.error(f"❌ Authorization error: {str(e)}")
            except RosterError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                import logging

                logging.exception("Unexpected error during user deletion")
