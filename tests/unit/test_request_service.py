"""Unit tests for RequestService."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.request import Request, RequestStatus
from app.models.user import UserRole
from app.services.request_service import (
    RequestService,
    get_request_service,
    RequestError,
    ValidationError,
    AuthorizationError,
)


@pytest.fixture
def request_service():
    """Get request service instance."""
    return get_request_service()


@pytest.fixture
def student_id():
    """Generate a student user ID."""
    return uuid4()


@pytest.fixture
def admin_id():
    """Generate an admin user ID."""
    return uuid4()


@pytest.fixture
def assistant_id():
    """Generate an assistant user ID."""
    return uuid4()


# Submit Request Tests

def test_submit_request_success(request_service, student_id):
    """Test successful request submission."""
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    assert request.id is not None
    assert request.user_id == student_id
    assert request.badge_name == "Python Fundamentals"
    assert request.status == RequestStatus.PENDING
    assert request.submitted_at is not None


def test_submit_request_empty_badge_name(request_service, student_id):
    """Test request submission with empty badge name."""
    with pytest.raises(ValidationError, match="Badge name is required"):
        request_service.submit_request(
            user_id=student_id,
            badge_name=""
        )


def test_submit_request_whitespace_badge_name(request_service, student_id):
    """Test request submission with whitespace-only badge name."""
    with pytest.raises(ValidationError, match="Badge name is required"):
        request_service.submit_request(
            user_id=student_id,
            badge_name="   "
        )


def test_submit_request_too_long_badge_name(request_service, student_id):
    """Test request submission with badge name over 200 characters."""
    long_name = "A" * 201
    with pytest.raises(ValidationError, match="200 characters or less"):
        request_service.submit_request(
            user_id=student_id,
            badge_name=long_name
        )


def test_submit_request_duplicate_pending(request_service, student_id):
    """Test that duplicate pending requests are prevented."""
    badge_name = "Python Fundamentals"

    # Submit first request
    request_service.submit_request(
        user_id=student_id,
        badge_name=badge_name
    )

    # Attempt to submit duplicate
    with pytest.raises(RequestError, match="already have a pending request"):
        request_service.submit_request(
            user_id=student_id,
            badge_name=badge_name
        )


def test_submit_request_allows_duplicate_after_decision(request_service, student_id, admin_id):
    """Test that duplicate requests are allowed after previous is decided."""
    badge_name = "Python Fundamentals"

    # Submit and approve first request
    request1 = request_service.submit_request(
        user_id=student_id,
        badge_name=badge_name
    )
    request_service.approve_request(
        request_id=request1.id,
        approver_id=admin_id,
        approver_role=UserRole.ADMIN
    )

    # Submit second request (should succeed)
    request2 = request_service.submit_request(
        user_id=student_id,
        badge_name=badge_name
    )

    assert request2.id != request1.id
    assert request2.status == RequestStatus.PENDING


# Approve Request Tests

def test_approve_request_success_by_admin(request_service, student_id, admin_id):
    """Test successful request approval by admin."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Approve request
    approved_request = request_service.approve_request(
        request_id=request.id,
        approver_id=admin_id,
        approver_role=UserRole.ADMIN,
        reason="Great work!"
    )

    assert approved_request.status == RequestStatus.APPROVED
    assert approved_request.decided_by == admin_id
    assert approved_request.decided_at is not None
    assert approved_request.decision_reason == "Great work!"


def test_approve_request_success_by_assistant(request_service, student_id, assistant_id):
    """Test successful request approval by assistant."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Approve request
    approved_request = request_service.approve_request(
        request_id=request.id,
        approver_id=assistant_id,
        approver_role=UserRole.ASSISTANT
    )

    assert approved_request.status == RequestStatus.APPROVED
    assert approved_request.decided_by == assistant_id


def test_approve_request_fails_for_student(request_service, student_id):
    """Test that students cannot approve requests."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Attempt to approve as student
    with pytest.raises(AuthorizationError, match="Only admins and assistants"):
        request_service.approve_request(
            request_id=request.id,
            approver_id=student_id,
            approver_role=UserRole.STUDENT
        )


def test_approve_request_not_found(request_service, admin_id):
    """Test approving a non-existent request."""
    fake_id = uuid4()
    with pytest.raises(RequestError, match="not found"):
        request_service.approve_request(
            request_id=fake_id,
            approver_id=admin_id,
            approver_role=UserRole.ADMIN
        )


def test_approve_request_already_approved(request_service, student_id, admin_id):
    """Test that already-approved requests cannot be re-approved."""
    # Submit and approve request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )
    request_service.approve_request(
        request_id=request.id,
        approver_id=admin_id,
        approver_role=UserRole.ADMIN
    )

    # Attempt to re-approve
    with pytest.raises(RequestError, match="cannot approve"):
        request_service.approve_request(
            request_id=request.id,
            approver_id=admin_id,
            approver_role=UserRole.ADMIN
        )


# Reject Request Tests

def test_reject_request_success(request_service, student_id, admin_id):
    """Test successful request rejection."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Reject request
    rejected_request = request_service.reject_request(
        request_id=request.id,
        approver_id=admin_id,
        approver_role=UserRole.ADMIN,
        reason="Insufficient evidence provided"
    )

    assert rejected_request.status == RequestStatus.REJECTED
    assert rejected_request.decided_by == admin_id
    assert rejected_request.decided_at is not None
    assert rejected_request.decision_reason == "Insufficient evidence provided"


def test_reject_request_requires_reason(request_service, student_id, admin_id):
    """Test that rejection requires a reason."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Attempt to reject without reason
    with pytest.raises(ValidationError, match="Reason is required"):
        request_service.reject_request(
            request_id=request.id,
            approver_id=admin_id,
            approver_role=UserRole.ADMIN,
            reason=""
        )


def test_reject_request_fails_for_student(request_service, student_id):
    """Test that students cannot reject requests."""
    # Submit request
    request = request_service.submit_request(
        user_id=student_id,
        badge_name="Python Fundamentals"
    )

    # Attempt to reject as student
    with pytest.raises(AuthorizationError, match="Only admins and assistants"):
        request_service.reject_request(
            request_id=request.id,
            approver_id=student_id,
            approver_role=UserRole.STUDENT,
            reason="No reason"
        )


# Query Tests

def test_get_user_requests(request_service, student_id):
    """Test getting user requests."""
    # Submit multiple requests
    request1 = request_service.submit_request(student_id, "Badge 1")
    request2 = request_service.submit_request(student_id, "Badge 2")

    # Get all user requests
    requests = request_service.get_user_requests(student_id)

    assert len(requests) == 2
    assert request1.id in [r.id for r in requests]
    assert request2.id in [r.id for r in requests]


def test_get_user_requests_with_status_filter(request_service, student_id, admin_id):
    """Test getting user requests filtered by status."""
    # Submit and approve one request
    request1 = request_service.submit_request(student_id, "Badge 1")
    request_service.approve_request(request1.id, admin_id, UserRole.ADMIN)

    # Submit pending request
    request_service.submit_request(student_id, "Badge 2")

    # Filter by pending
    pending = request_service.get_user_requests(student_id, status_filter=RequestStatus.PENDING)
    assert len(pending) == 1

    # Filter by approved
    approved = request_service.get_user_requests(student_id, status_filter=RequestStatus.APPROVED)
    assert len(approved) == 1


def test_get_pending_requests(request_service, student_id, admin_id):
    """Test getting all pending requests."""
    # Submit requests
    request1 = request_service.submit_request(student_id, "Badge 1")
    request2 = request_service.submit_request(student_id, "Badge 2")
    request3 = request_service.submit_request(student_id, "Badge 3")

    # Approve one
    request_service.approve_request(request1.id, admin_id, UserRole.ADMIN)

    # Get pending requests
    pending = request_service.get_pending_requests()

    assert len(pending) == 2
    assert request2.id in [r.id for r in pending]
    assert request3.id in [r.id for r in pending]


def test_count_pending_requests(request_service, student_id, admin_id):
    """Test counting pending requests."""
    # Submit requests
    request1 = request_service.submit_request(student_id, "Badge 1")
    request_service.submit_request(student_id, "Badge 2")
    request_service.submit_request(student_id, "Badge 3")

    # Approve one
    request_service.approve_request(request1.id, admin_id, UserRole.ADMIN)

    # Count pending
    count = request_service.count_pending_requests()
    assert count == 2


def test_get_request_by_id(request_service, student_id):
    """Test getting a specific request by ID."""
    request = request_service.submit_request(student_id, "Python Fundamentals")

    fetched = request_service.get_request_by_id(request.id)

    assert fetched is not None
    assert fetched.id == request.id
    assert fetched.badge_name == "Python Fundamentals"


def test_get_request_by_id_not_found(request_service):
    """Test getting a non-existent request."""
    fake_id = uuid4()
    fetched = request_service.get_request_by_id(fake_id)
    assert fetched is None
