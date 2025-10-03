"""Request form UI component for badge submission."""

import streamlit as st

from app.models.user import User
from app.services.request_service import (
    RequestError,
    ValidationError,
    get_request_service,
)
from app.ui.badge_picker import render_badge_picker


def render_request_form(user: User) -> None:
    """
    Render badge request submission form for students.

    Args:
        user: Current logged-in student user
    """
    st.markdown("### 📝 Request a Badge")
    st.markdown(
        "Select a badge from the catalog below. Your request will be reviewed "
        "by instructors and assistants."
    )

    with st.form("badge_request_form", clear_on_submit=True):
        # Use badge picker (Phase 5+)
        mini_badge_id = render_badge_picker(key_prefix="request_form")

        submitted = st.form_submit_button(
            "Submit Request",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            # Validate input
            if not mini_badge_id:
                st.error("❌ Please select a badge to request")
                return

            # Submit request
            try:
                request_service = get_request_service()
                request = request_service.submit_request(
                    user_id=user.id,
                    mini_badge_id=mini_badge_id,
                )

                st.success(
                    f"✅ Request submitted successfully! "
                    f"Request ID: `{request.id}`"
                )
                st.info(
                    "Your request is now pending review. You'll be notified when a "
                    "decision is made."
                )

                # Force rerun to refresh request history
                st.rerun()

            except ValidationError as e:
                st.error(f"❌ Validation error: {str(e)}")
            except RequestError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                import logging
                logging.exception("Unexpected error during request submission")


def render_user_requests(user: User) -> None:
    """
    Render the current user's request history.

    Args:
        user: Current logged-in user
    """
    st.markdown("### 📋 My Badge Requests")

    request_service = get_request_service()

    # Get all user requests
    all_requests = request_service.get_user_requests(user_id=user.id, limit=100)

    if not all_requests:
        st.info("You haven't submitted any badge requests yet.")
        return

    # Filter tabs
    tab_all, tab_pending, tab_approved, tab_rejected = st.tabs([
        f"All ({len(all_requests)})",
        f"Pending ({sum(1 for r in all_requests if r.is_pending())})",
        f"Approved ({sum(1 for r in all_requests if r.is_approved())})",
        f"Rejected ({sum(1 for r in all_requests if r.is_rejected())})",
    ])

    with tab_all:
        _render_request_list(all_requests)

    with tab_pending:
        pending_requests = [r for r in all_requests if r.is_pending()]
        if pending_requests:
            _render_request_list(pending_requests)
        else:
            st.info("No pending requests")

    with tab_approved:
        approved_requests = [r for r in all_requests if r.is_approved()]
        if approved_requests:
            _render_request_list(approved_requests)
        else:
            st.info("No approved requests")

    with tab_rejected:
        rejected_requests = [r for r in all_requests if r.is_rejected()]
        if rejected_requests:
            _render_request_list(rejected_requests)
        else:
            st.info("No rejected requests")


def _render_request_list(requests: list) -> None:
    """
    Render a list of requests as a table.

    Args:
        requests: List of Request objects to display
    """
    for request in requests:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{request.badge_name}**")

            with col2:
                # Status badge
                if request.is_pending():
                    st.markdown("🟡 **Pending**")
                elif request.is_approved():
                    st.markdown("🟢 **Approved**")
                elif request.is_rejected():
                    st.markdown("🔴 **Rejected**")

            with col3:
                st.caption(f"Submitted: {request.submitted_at.strftime('%Y-%m-%d %H:%M')}")

            # Show decision details if decided
            if request.is_decided():
                st.caption(
                    f"Decided: {request.decided_at.strftime('%Y-%m-%d %H:%M')}"
                )
                if request.decision_reason:
                    st.info(f"**Reason:** {request.decision_reason}")

            st.markdown("---")
