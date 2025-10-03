"""Request model for badge approval workflow."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class RequestStatus(str, Enum):
    """Request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Request(SQLModel, table=True):
    """Badge request model for approval workflow."""

    __tablename__ = "requests"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Student who submitted the request
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Badge being requested (placeholder for Phase 4, will be FK to mini_badges in Phase 5)
    mini_badge_id: UUID | None = Field(default=None)
    badge_name: str = Field(max_length=200)  # Temporary field for Phase 4

    # Request status
    status: RequestStatus = Field(default=RequestStatus.PENDING, index=True)

    # Submission tracking
    submitted_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Decision tracking
    decided_at: datetime | None = Field(default=None)
    decided_by: UUID | None = Field(default=None, foreign_key="users.id")
    decision_reason: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == RequestStatus.PENDING

    def is_decided(self) -> bool:
        """Check if request has been decided (approved or rejected)."""
        return self.status in (RequestStatus.APPROVED, RequestStatus.REJECTED)

    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == RequestStatus.APPROVED

    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == RequestStatus.REJECTED
