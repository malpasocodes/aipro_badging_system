"""Roster service for user management."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class RosterError(Exception):
    """Base exception for roster-related errors."""

    pass


class AuthorizationError(RosterError):
    """Authorization-related errors."""

    pass


class RosterService:
    """Service for managing user roster and roles."""

    def __init__(self):
        self.audit_service = get_audit_service()

    def get_all_users(
        self,
        role_filter: UserRole | None = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        Get all users with optional filtering.

        Args:
            role_filter: Optional filter by role (admin/assistant/student)
            include_inactive: Whether to include inactive users
            limit: Maximum number of results (default 100)
            offset: Number of results to skip

        Returns:
            List of User objects, ordered by username
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(User)

            if role_filter is not None:
                statement = statement.where(User.role == role_filter)

            if not include_inactive:
                statement = statement.where(User.is_active)

            statement = statement.order_by(User.username).limit(limit).offset(offset)

            results = session.exec(statement).all()
            return list(results)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """
        Get a specific user by ID.

        Args:
            user_id: UUID of the user

        Returns:
            User object if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).first()

    def get_user_by_email(self, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(User).where(User.email == email.lower())
            return session.exec(statement).first()

    def get_user_stats(self) -> dict[str, int]:
        """
        Get user statistics by role.

        Returns:
            Dictionary with counts: {
                "total": int,
                "admins": int,
                "assistants": int,
                "students": int,
                "active": int,
                "inactive": int
            }
        """
        engine = get_engine()

        with Session(engine) as session:
            all_users = session.exec(select(User)).all()

            # Count only active users for role statistics
            stats = {
                "total": sum(1 for u in all_users if u.is_active),
                "admins": sum(
                    1 for u in all_users if u.role == UserRole.ADMIN and u.is_active
                ),
                "assistants": sum(
                    1 for u in all_users if u.role == UserRole.ASSISTANT and u.is_active
                ),
                "students": sum(
                    1 for u in all_users if u.role == UserRole.STUDENT and u.is_active
                ),
                "active": sum(1 for u in all_users if u.is_active),
                "inactive": sum(1 for u in all_users if not u.is_active),
            }

            return stats

    def update_user_role(
        self,
        user_id: UUID,
        new_role: UserRole,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> User:
        """
        Update a user's role (admin-only operation).

        Args:
            user_id: ID of user whose role is being updated
            new_role: New role to assign
            actor_id: ID of admin performing the update
            actor_role: Role of the actor (for authorization check)

        Returns:
            Updated User object

        Raises:
            RosterError: If user not found
            AuthorizationError: If actor is not an admin
        """
        # Check authorization - only admins can update roles
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can update user roles")

        engine = get_engine()

        with Session(engine) as session:
            # Get user
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()

            if not user:
                raise RosterError(f"User {user_id} not found")

            # Update role
            old_role = user.role
            if old_role == new_role:
                logger.info(
                    "No role change needed",
                    user_id=str(user_id),
                    role=new_role.value,
                )
                return user

            user.role = new_role
            user.updated_at = datetime.utcnow()

            session.add(user)
            session.commit()
            session.refresh(user)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="update_user_role",
                entity="user",
                entity_id=user_id,
                context_data={
                    "user_id": str(user_id),
                    "email": user.email,
                    "old_role": old_role.value,
                    "new_role": new_role.value,
                },
            )

            logger.info(
                "User role updated",
                user_id=str(user_id),
                email=user.email,
                old_role=old_role.value,
                new_role=new_role.value,
                actor_id=str(actor_id),
            )

            return user

    def toggle_user_active_status(
        self,
        user_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> User:
        """
        Toggle a user's active status (admin-only operation).

        Args:
            user_id: ID of user whose status is being toggled
            actor_id: ID of admin performing the update
            actor_role: Role of the actor (for authorization check)

        Returns:
            Updated User object

        Raises:
            RosterError: If user not found
            AuthorizationError: If actor is not an admin
        """
        # Check authorization - only admins can toggle active status
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can toggle user active status")

        engine = get_engine()

        with Session(engine) as session:
            # Get user
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()

            if not user:
                raise RosterError(f"User {user_id} not found")

            # Toggle active status
            old_status = user.is_active
            user.is_active = not user.is_active
            user.updated_at = datetime.utcnow()

            session.add(user)
            session.commit()
            session.refresh(user)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="toggle_user_active_status",
                entity="user",
                entity_id=user_id,
                context_data={
                    "user_id": str(user_id),
                    "email": user.email,
                    "old_status": "active" if old_status else "inactive",
                    "new_status": "active" if user.is_active else "inactive",
                },
            )

            logger.info(
                "User active status toggled",
                user_id=str(user_id),
                email=user.email,
                old_status=old_status,
                new_status=user.is_active,
                actor_id=str(actor_id),
            )

            return user

    def count_users(self, role_filter: UserRole | None = None) -> int:
        """
        Count users with optional role filter.

        Args:
            role_filter: Optional filter by role

        Returns:
            Count of matching users
        """
        engine = get_engine()

        with Session(engine) as session:
            statement = select(User)

            if role_filter is not None:
                statement = statement.where(User.role == role_filter)

            results = session.exec(statement).all()
            return len(results)

    def create_user(
        self,
        email: str,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> User:
        """
        Create a new user with Student role (admin-only operation).

        Args:
            email: User's email address
            actor_id: ID of admin performing the creation
            actor_role: Role of the actor (for authorization check)

        Returns:
            Created User object

        Raises:
            RosterError: If user creation fails or user already exists
            AuthorizationError: If actor is not an admin
        """
        # Check authorization - only admins can create users
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can create users")

        # Normalize email
        email = email.lower().strip()

        engine = get_engine()

        with Session(engine) as session:
            # Check if user already exists
            statement = select(User).where(User.email == email)
            existing_user = session.exec(statement).first()

            if existing_user:
                raise RosterError(f"User with email {email} already exists")

            # Create new user with Student role
            # Note: google_sub will be set when they first login via OAuth
            new_user = User(
                email=email,
                role=UserRole.STUDENT,  # All new users start as students
                is_active=True,
                google_sub=f"manual_create_{email}",  # Temporary, will be updated on first login
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="create_user",
                entity="user",
                entity_id=new_user.id,
                context_data={
                    "user_id": str(new_user.id),
                    "email": email,
                    "role": UserRole.STUDENT.value,
                    "created_by": "admin",
                },
            )

            logger.info(
                "User created",
                user_id=str(new_user.id),
                email=email,
                role=UserRole.STUDENT.value,
                actor_id=str(actor_id),
            )

            return new_user

    def delete_user(
        self,
        user_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> User:
        """
        Delete (deactivate) a user (admin-only operation).

        This is a soft delete - sets is_active to False.

        Args:
            user_id: ID of user to delete
            actor_id: ID of admin performing the deletion
            actor_role: Role of the actor (for authorization check)

        Returns:
            Deleted (deactivated) User object

        Raises:
            RosterError: If user not found or cannot be deleted
            AuthorizationError: If actor is not an admin
        """
        # Check authorization - only admins can delete users
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can delete users")

        engine = get_engine()

        with Session(engine) as session:
            # Get user
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()

            if not user:
                raise RosterError(f"User {user_id} not found")

            if not user.is_active:
                raise RosterError(f"User {user.email} is already inactive")

            # Soft delete - deactivate user
            user.is_active = False
            user.updated_at = datetime.utcnow()

            session.add(user)
            session.commit()
            session.refresh(user)

            # Create audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="delete_user",
                entity="user",
                entity_id=user_id,
                context_data={
                    "user_id": str(user_id),
                    "email": user.email,
                    "role": user.role.value,
                    "deleted_by": "admin",
                },
            )

            logger.info(
                "User deleted (deactivated)",
                user_id=str(user_id),
                email=user.email,
                actor_id=str(actor_id),
            )

            return user


# Service factory function
def get_roster_service() -> RosterService:
    """Get an instance of RosterService."""
    return RosterService()
