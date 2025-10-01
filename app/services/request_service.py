"""Request service for badge approval workflow."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.request import Request, RequestStatus
from app.models.user import User, UserRole
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class RequestError(Exception):
    """Base exception for request-related errors."""
    pass


class ValidationError(RequestError):
    """Validation-related errors."""
    pass


class AuthorizationError(RequestError):
    """Authorization-related errors."""
    pass


class RequestService:
    """Service for managing badge requests and approval workflow."""

    def __init__(self):
        self.audit_service = get_audit_service()

    def submit_request(self, user_id: UUID, badge_name: str) -> Request:
        """
        Submit a new badge request.

        Args:
            user_id: ID of the student submitting the request
            badge_name: Name of the badge being requested (placeholder for Phase 4)

        Returns:
            Created Request object

        Raises:
            ValidationError: If badge_name is empty or invalid
            RequestError: If user has pending request for same badge

        Example:
            >>> service = get_request_service()
            >>> request = service.submit_request(student_id, "Python Fundamentals")
        """
        # Validate badge_name
        if not badge_name or not badge_name.strip():
            raise ValidationError("Badge name is required")

        badge_name = badge_name.strip()

        if len(badge_name) > 200:
            raise ValidationError("Badge name must be 200 characters or less")

        engine = get_engine()

        with Session(engine) as session:
            # Check for existing pending request for same badge
            statement = (
                select(Request)
                .where(Request.user_id == user_id)
                .where(Request.badge_name == badge_name)
                .where(Request.status == RequestStatus.PENDING)
            )
            existing_request = session.exec(statement).first()

            if existing_request:
                raise RequestError(
                    f"You already have a pending request for '{badge_name}'"
                )

            # Create new request
            request = Request(
                user_id=user_id,
                badge_name=badge_name,
                status=RequestStatus.PENDING,
            )

            session.add(request)
            session.commit()
            session.refresh(request)

            logger.info(
                "Badge request submitted",
                request_id=str(request.id),
                user_id=str(user_id),
                badge_name=badge_name,
            )

            return request

    def get_user_requests(
        self,
        user_id: UUID,
        status_filter: Optional[RequestStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Request]:
        """
        Get all requests submitted by a specific user.

        Args:
            user_id: ID of the user
            status_filter: Optional filter by status (pending/approved/rejected)
            limit: Maximum number of results (default 50)
            offset: Number of results to skip

        Returns:
            List of Request objects, ordered by submitted_at DESC
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(Request).where(Request.user_id == user_id)

            if status_filter is not None:
                statement = statement.where(Request.status == status_filter)

            statement = (
                statement.order_by(Request.submitted_at.desc())
                .limit(limit)
                .offset(offset)
            )

            results = session.exec(statement).all()
            return list(results)

    def get_pending_requests(
        self,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Request]:
        """
        Get all pending requests (approval queue).

        Args:
            limit: Maximum number of results (default 25)
            offset: Number of results to skip

        Returns:
            List of pending Request objects, ordered by submitted_at ASC (oldest first)
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = (
                select(Request)
                .where(Request.status == RequestStatus.PENDING)
                .order_by(Request.submitted_at.asc())  # Oldest first for queue
                .limit(limit)
                .offset(offset)
            )

            results = session.exec(statement).all()
            return list(results)

    def get_all_requests(
        self,
        status_filter: Optional[RequestStatus] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Request]:
        """
        Get all requests with optional status filter (admin view).

        Args:
            status_filter: Optional filter by status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Request objects, ordered by submitted_at DESC
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(Request)

            if status_filter is not None:
                statement = statement.where(Request.status == status_filter)

            statement = (
                statement.order_by(Request.submitted_at.desc())
                .limit(limit)
                .offset(offset)
            )

            results = session.exec(statement).all()
            return list(results)

    def get_request_by_id(self, request_id: UUID) -> Optional[Request]:
        """
        Get a specific request by ID.

        Args:
            request_id: UUID of the request

        Returns:
            Request object if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(Request).where(Request.id == request_id)
            return session.exec(statement).first()

    def approve_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        approver_role: UserRole,
        reason: Optional[str] = None,
    ) -> Request:
        """
        Approve a pending badge request.

        Args:
            request_id: ID of the request to approve
            approver_id: ID of the admin/assistant approving the request
            approver_role: Role of the approver (for authorization check)
            reason: Optional reason for approval

        Returns:
            Updated Request object

        Raises:
            RequestError: If request not found or not pending
            AuthorizationError: If approver doesn't have permission
        """
        # Check authorization
        if approver_role not in (UserRole.ADMIN, UserRole.ASSISTANT):
            raise AuthorizationError(
                "Only admins and assistants can approve requests"
            )

        engine = get_engine()

        with Session(engine) as session:
            # Get request
            statement = select(Request).where(Request.id == request_id)
            request = session.exec(statement).first()

            if not request:
                raise RequestError(f"Request {request_id} not found")

            if request.status != RequestStatus.PENDING:
                raise RequestError(
                    f"Request is {request.status.value}, cannot approve"
                )

            # Update request
            old_status = request.status
            request.status = RequestStatus.APPROVED
            request.decided_at = datetime.utcnow()
            request.decided_by = approver_id
            request.decision_reason = reason
            request.updated_at = datetime.utcnow()

            session.add(request)
            session.commit()
            session.refresh(request)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=approver_id,
                action="approve_request",
                entity="request",
                entity_id=request_id,
                context_data={
                    "request_id": str(request_id),
                    "badge_name": request.badge_name,
                    "student_id": str(request.user_id),
                    "old_status": old_status.value,
                    "new_status": RequestStatus.APPROVED.value,
                    "reason": reason,
                },
            )

            logger.info(
                "Request approved",
                request_id=str(request_id),
                approver_id=str(approver_id),
                badge_name=request.badge_name,
                student_id=str(request.user_id),
            )

            return request

    def reject_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        approver_role: UserRole,
        reason: str,
    ) -> Request:
        """
        Reject a pending badge request.

        Args:
            request_id: ID of the request to reject
            approver_id: ID of the admin/assistant rejecting the request
            approver_role: Role of the approver (for authorization check)
            reason: Reason for rejection (required)

        Returns:
            Updated Request object

        Raises:
            RequestError: If request not found or not pending
            AuthorizationError: If approver doesn't have permission
            ValidationError: If reason is missing
        """
        # Check authorization
        if approver_role not in (UserRole.ADMIN, UserRole.ASSISTANT):
            raise AuthorizationError(
                "Only admins and assistants can reject requests"
            )

        # Validate reason is provided
        if not reason or not reason.strip():
            raise ValidationError("Reason is required for rejection")

        engine = get_engine()

        with Session(engine) as session:
            # Get request
            statement = select(Request).where(Request.id == request_id)
            request = session.exec(statement).first()

            if not request:
                raise RequestError(f"Request {request_id} not found")

            if request.status != RequestStatus.PENDING:
                raise RequestError(
                    f"Request is {request.status.value}, cannot reject"
                )

            # Update request
            old_status = request.status
            request.status = RequestStatus.REJECTED
            request.decided_at = datetime.utcnow()
            request.decided_by = approver_id
            request.decision_reason = reason.strip()
            request.updated_at = datetime.utcnow()

            session.add(request)
            session.commit()
            session.refresh(request)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=approver_id,
                action="reject_request",
                entity="request",
                entity_id=request_id,
                context_data={
                    "request_id": str(request_id),
                    "badge_name": request.badge_name,
                    "student_id": str(request.user_id),
                    "old_status": old_status.value,
                    "new_status": RequestStatus.REJECTED.value,
                    "reason": reason.strip(),
                },
            )

            logger.info(
                "Request rejected",
                request_id=str(request_id),
                approver_id=str(approver_id),
                badge_name=request.badge_name,
                student_id=str(request.user_id),
                reason=reason.strip(),
            )

            return request

    def count_pending_requests(self) -> int:
        """
        Count the number of pending requests.

        Returns:
            Count of pending requests
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(Request).where(Request.status == RequestStatus.PENDING)
            results = session.exec(statement).all()
            return len(results)


# Service factory function
def get_request_service() -> RequestService:
    """Get an instance of RequestService."""
    return RequestService()
