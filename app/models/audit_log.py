"""Audit log model for tracking privileged operations."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    """Audit log for tracking privileged operations and decisions."""

    __tablename__ = "audit_logs"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Actor (user who performed the action)
    actor_user_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )

    # Action details
    action: str = Field(max_length=100)  # approve_request, reject_request, update_role, etc.
    entity: str = Field(max_length=50, index=True)  # request, user, etc.
    entity_id: UUID = Field(index=True)  # ID of the entity being acted upon

    # Flexible context data storage (old values, reasons, additional info, etc.)
    # Note: Field named "context_data" instead of "metadata" to avoid SQLAlchemy reserved name
    context_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # Timestamp (append-only, no updates)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """SQLModel configuration."""
        arbitrary_types_allowed = True
