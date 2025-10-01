"""Audit logging service for tracking privileged operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.audit_log import AuditLog

logger = get_logger(__name__)


class AuditService:
    """Service for logging and querying audit trails of privileged operations."""

    def log_action(
        self,
        actor_user_id: Optional[UUID],
        action: str,
        entity: str,
        entity_id: UUID,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log a privileged action to the audit trail.

        Args:
            actor_user_id: ID of user performing the action (None for system actions)
            action: Description of action (e.g., "approve_request", "reject_request")
            entity: Type of entity being acted upon (e.g., "request", "user")
            entity_id: ID of the entity
            context_data: Additional context (reasons, old values, etc.)

        Returns:
            Created AuditLog entry

        Example:
            >>> service = get_audit_service()
            >>> service.log_action(
            ...     actor_user_id=admin_id,
            ...     action="approve_request",
            ...     entity="request",
            ...     entity_id=request_id,
            ...     context_data={"reason": "Completed successfully", "status": "approved"}
            ... )
        """
        engine = get_engine()

        with Session(engine) as session:
            audit_log = AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                context_data=context_data,
            )

            session.add(audit_log)
            session.commit()
            session.refresh(audit_log)

            logger.info(
                "Audit log created",
                audit_log_id=str(audit_log.id),
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                action=action,
                entity=entity,
                entity_id=str(entity_id),
            )

            return audit_log

    def get_audit_logs(
        self,
        entity: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Query audit logs with optional filters.

        Args:
            entity: Filter by entity type (e.g., "request", "user")
            entity_id: Filter by specific entity ID
            actor_user_id: Filter by user who performed action
            limit: Maximum number of results (default 100, max 1000)
            offset: Number of results to skip for pagination

        Returns:
            List of matching AuditLog entries, ordered by created_at DESC

        Example:
            >>> # Get all audit logs for a specific request
            >>> logs = service.get_audit_logs(entity="request", entity_id=request_id)
            >>>
            >>> # Get all actions by a specific admin
            >>> logs = service.get_audit_logs(actor_user_id=admin_id, limit=50)
        """
        # Enforce maximum limit
        limit = min(limit, 1000)

        engine = get_engine()

        with Session(engine) as session:
            # Build query with optional filters
            statement = select(AuditLog)

            if entity is not None:
                statement = statement.where(AuditLog.entity == entity)

            if entity_id is not None:
                statement = statement.where(AuditLog.entity_id == entity_id)

            if actor_user_id is not None:
                statement = statement.where(AuditLog.actor_user_id == actor_user_id)

            # Order by created_at descending (newest first)
            statement = statement.order_by(AuditLog.created_at.desc())

            # Apply pagination
            statement = statement.limit(limit).offset(offset)

            # Execute query
            results = session.exec(statement).all()

            logger.debug(
                "Audit logs queried",
                entity=entity,
                entity_id=str(entity_id) if entity_id else None,
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                count=len(results),
            )

            return list(results)

    def get_audit_log_by_id(self, audit_log_id: UUID) -> Optional[AuditLog]:
        """
        Get a specific audit log entry by ID.

        Args:
            audit_log_id: UUID of the audit log entry

        Returns:
            AuditLog if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(AuditLog).where(AuditLog.id == audit_log_id)
            return session.exec(statement).first()

    def count_audit_logs(
        self,
        entity: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_user_id: Optional[UUID] = None,
    ) -> int:
        """
        Count audit logs matching filters.

        Args:
            entity: Filter by entity type
            entity_id: Filter by specific entity ID
            actor_user_id: Filter by user who performed action

        Returns:
            Count of matching audit log entries
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(AuditLog)

            if entity is not None:
                statement = statement.where(AuditLog.entity == entity)

            if entity_id is not None:
                statement = statement.where(AuditLog.entity_id == entity_id)

            if actor_user_id is not None:
                statement = statement.where(AuditLog.actor_user_id == actor_user_id)

            results = session.exec(statement).all()
            return len(results)


# Service factory function
def get_audit_service() -> AuditService:
    """Get an instance of AuditService."""
    return AuditService()
