"""Approval queue UI component for admin and assistant roles."""

import streamlit as st

from app.models.user import User
from app.models.request import Request, RequestStatus
from app.services.request_service import (
    get_request_service,
    RequestError,
    ValidationError,
    AuthorizationError,
)
from app.services.roster_service import get_roster_service


def render_approval_queue(user: User) -> None:
    """
    Render the badge approval queue for admins/assistants.

    Args:
        user: Current logged-in user (admin or assistant)
    """
    st.markdown("### 📋 Badge Approval Queue")

    request_service = get_request_service()
    roster_service = get_roster_service()

    # Get pending count
    pending_count = request_service.count_pending_requests()

    # Show metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Pending Requests", pending_count)
    with col2:
        total_count = len(request_service.get_all_requests(limit=1000))
        st.metric("Total Requests", total_count)

    # View selector
    view_option = st.radio(
        "View",
        ["Pending Only", "All Requests"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if view_option == "Pending Only":
        requests = request_service.get_pending_requests(limit=100)
        if not requests:
            st.info("✅ No pending requests! The queue is clear.")
            return
    else:
        # Show all requests with status filter
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Approved", "Rejected"],
        )

        if status_filter == "All":
            requests = request_service.get_all_requests(limit=100)
        elif status_filter == "Pending":
            requests = request_service.get_all_requests(
                status_filter=RequestStatus.PENDING,
                limit=100
            )
        elif status_filter == "Approved":
            requests = request_service.get_all_requests(
                status_filter=RequestStatus.APPROVED,
                limit=100
            )
        else:  # Rejected
            requests = request_service.get_all_requests(
                status_filter=RequestStatus.REJECTED,
                limit=100
            )

        if not requests:
            st.info(f"No {status_filter.lower()} requests found.")
            return

    # Display requests
    st.markdown(f"**Showing {len(requests)} request(s)**")
    st.markdown("---")

    # Get all users for student name lookup
    all_users = {u.id: u for u in roster_service.get_all_users(limit=1000)}

    for request in requests:
        _render_request_card(request, user, all_users)


def _render_request_card(request: Request, current_user: User, all_users: dict) -> None:
    """
    Render a single request card with approve/reject actions.

    Args:
        request: Request object to display
        current_user: Current logged-in user (admin/assistant)
        all_users: Dictionary of user_id -> User for lookups
    """
    with st.container():
        # Header
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            # Student name
            student = all_users.get(request.user_id)
            student_name = student.username if student and student.username else student.email if student else "Unknown"
            st.markdown(f"**Student:** {student_name}")
            st.markdown(f"**Badge:** {request.badge_name}")

        with col2:
            # Status
            if request.is_pending():
                st.markdown("🟡 **Pending**")
            elif request.is_approved():
                st.markdown("🟢 **Approved**")
            elif request.is_rejected():
                st.markdown("🔴 **Rejected**")

        with col3:
            st.caption(f"Submitted: {request.submitted_at.strftime('%Y-%m-%d')}")
            st.caption(f"ID: `{str(request.id)[:8]}...`")

        # Decision details (if decided)
        if request.is_decided():
            decider = all_users.get(request.decided_by) if request.decided_by else None
            decider_name = decider.username if decider and decider.username else decider.email if decider else "System"

            st.caption(f"Decided by: {decider_name} on {request.decided_at.strftime('%Y-%m-%d %H:%M')}")
            if request.decision_reason:
                st.info(f"**Reason:** {request.decision_reason}")

        # Action buttons (only for pending requests)
        if request.is_pending():
            col1, col2, col3 = st.columns([1, 1, 4])

            with col1:
                if st.button(
                    "✅ Approve",
                    key=f"approve_{request.id}",
                    use_container_width=True,
                ):
                    _handle_approve(request, current_user)

            with col2:
                if st.button(
                    "❌ Reject",
                    key=f"reject_{request.id}",
                    use_container_width=True,
                ):
                    # Store request ID in session state to show reject modal
                    st.session_state[f"reject_modal_{request.id}"] = True
                    st.rerun()

            # Reject modal (show if triggered)
            if st.session_state.get(f"reject_modal_{request.id}", False):
                _show_reject_modal(request, current_user)

        st.markdown("---")


def _handle_approve(request: Request, current_user: User) -> None:
    """
    Handle approve button click.

    Args:
        request: Request to approve
        current_user: Current user approving the request
    """
    try:
        request_service = get_request_service()
        request_service.approve_request(
            request_id=request.id,
            approver_id=current_user.id,
            approver_role=current_user.role,
            reason=None,
        )

        st.success(f"✅ Request approved for '{request.badge_name}'!")
        st.rerun()

    except AuthorizationError as e:
        st.error(f"❌ Authorization error: {str(e)}")
    except RequestError as e:
        st.error(f"❌ {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        import logging
        logging.exception("Unexpected error during approval")


@st.dialog("Reject Request")
def _show_reject_modal(request: Request, current_user: User) -> None:
    """
    Show modal dialog for rejecting a request with reason.

    Args:
        request: Request to reject
        current_user: Current user rejecting the request
    """
    st.markdown(f"**Badge:** {request.badge_name}")
    st.markdown("---")

    reason = st.text_area(
        "Reason for rejection *",
        placeholder="Please provide a clear reason for rejection...",
        help="This reason will be visible to the student",
        max_chars=500,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancel", use_container_width=True):
            # Clear modal state
            st.session_state[f"reject_modal_{request.id}"] = False
            st.rerun()

    with col2:
        if st.button("Confirm Rejection", type="primary", use_container_width=True):
            if not reason or not reason.strip():
                st.error("❌ Reason is required for rejection")
                return

            try:
                request_service = get_request_service()
                request_service.reject_request(
                    request_id=request.id,
                    approver_id=current_user.id,
                    approver_role=current_user.role,
                    reason=reason.strip(),
                )

                # Clear modal state
                st.session_state[f"reject_modal_{request.id}"] = False

                st.success(f"✅ Request rejected for '{request.badge_name}'")
                st.rerun()

            except ValidationError as e:
                st.error(f"❌ Validation error: {str(e)}")
            except AuthorizationError as e:
                st.error(f"❌ Authorization error: {str(e)}")
            except RequestError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                import logging
                logging.exception("Unexpected error during rejection")
