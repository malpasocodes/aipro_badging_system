"""Onboarding service for capturing user information after authentication."""

import re
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


class OnboardingError(Exception):
    """Onboarding-related errors."""

    pass


class ValidationError(OnboardingError):
    """Validation errors during onboarding."""

    pass


class OnboardingService:
    """Service for managing user onboarding."""

    # Email validation regex (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
        r"[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    # Username validation regex
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(self) -> None:
        """Initialize onboarding service."""
        self.settings = get_settings()

    def check_onboarding_status(self, user: User) -> bool:
        """
        Check if user has completed onboarding.

        Args:
            user: User object to check

        Returns:
            True if user has completed onboarding, False otherwise
        """
        return user.is_onboarded()

    def complete_onboarding(
        self,
        user_id: UUID,
        username: str,
        substack_email: str,
        meetup_email: str,
    ) -> User:
        """
        Complete onboarding for a user.

        Args:
            user_id: UUID of the user
            username: Display name (3-50 characters)
            substack_email: Substack subscription email
            meetup_email: Meetup email address

        Returns:
            Updated User object

        Raises:
            ValidationError: If any field fails validation
            OnboardingError: If user not found or database error
        """
        # Validate all inputs
        self._validate_username(username)
        self._validate_email(substack_email, "Substack email")
        self._validate_email(meetup_email, "Meetup email")

        engine = get_engine()

        with Session(engine) as session:
            # Get user
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()

            if not user:
                raise OnboardingError(f"User not found: {user_id}")

            # Check if already onboarded
            if user.is_onboarded():
                logger.warning(
                    "User already onboarded",
                    user_id=str(user.id),
                    email=user.email,
                )
                return user

            # Update user with onboarding data
            user.username = username.strip()
            user.substack_email = substack_email.strip().lower()
            user.meetup_email = meetup_email.strip().lower()
            user.onboarding_completed_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()

            session.add(user)
            session.commit()
            session.refresh(user)

            logger.info(
                "Onboarding completed",
                user_id=str(user.id),
                email=user.email,
                username=username,
            )

            return user

    def _validate_username(self, username: str) -> None:
        """
        Validate username meets requirements.

        Args:
            username: Username to validate

        Raises:
            ValidationError: If validation fails
        """
        if not username:
            raise ValidationError("Username is required")

        # Strip whitespace for validation
        username = username.strip()

        # Check if empty after stripping
        if not username:
            raise ValidationError("Username is required")

        # Length check
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")

        if len(username) > 50:
            raise ValidationError("Username must not exceed 50 characters")

        # Character check
        if not self.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        # Leading/trailing special characters
        if username[0] in "_-" or username[-1] in "_-":
            raise ValidationError(
                "Username cannot start or end with underscore or hyphen"
            )

    def _validate_email(self, email: str, field_name: str = "Email") -> None:
        """
        Validate email format.

        Args:
            email: Email address to validate
            field_name: Name of the field (for error messages)

        Raises:
            ValidationError: If validation fails
        """
        if not email:
            raise ValidationError(f"{field_name} is required")

        # Strip whitespace
        email = email.strip()

        # Check if empty after stripping
        if not email:
            raise ValidationError(f"{field_name} is required")

        # Length check
        if len(email) > 254:  # RFC 5321
            raise ValidationError(f"{field_name} is too long")

        # Format check (catches most invalid formats including double @@)
        if not self.EMAIL_PATTERN.match(email):
            raise ValidationError(f"{field_name} is not a valid email address")

        local, domain = email.split("@")

        if not local or not domain:
            raise ValidationError(f"{field_name} is not a valid email address")

        if len(local) > 64:  # RFC 5321
            raise ValidationError(f"{field_name} local part is too long")

    def update_onboarding_info(
        self,
        user_id: UUID,
        username: str | None = None,
        substack_email: str | None = None,
        meetup_email: str | None = None,
    ) -> User:
        """
        Update onboarding information for a user who has already completed onboarding.

        Args:
            user_id: UUID of the user
            username: New username (optional)
            substack_email: New Substack email (optional)
            meetup_email: New Meetup email (optional)

        Returns:
            Updated User object

        Raises:
            ValidationError: If any field fails validation
            OnboardingError: If user not found or not yet onboarded
        """
        # Validate provided fields
        if username is not None:
            self._validate_username(username)
        if substack_email is not None:
            self._validate_email(substack_email, "Substack email")
        if meetup_email is not None:
            self._validate_email(meetup_email, "Meetup email")

        engine = get_engine()

        with Session(engine) as session:
            # Get user
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()

            if not user:
                raise OnboardingError(f"User not found: {user_id}")

            if not user.is_onboarded():
                raise OnboardingError("User has not completed onboarding yet")

            # Update provided fields
            if username is not None:
                user.username = username.strip()
            if substack_email is not None:
                user.substack_email = substack_email.strip().lower()
            if meetup_email is not None:
                user.meetup_email = meetup_email.strip().lower()

            user.updated_at = datetime.utcnow()

            session.add(user)
            session.commit()
            session.refresh(user)

            logger.info(
                "Onboarding info updated",
                user_id=str(user.id),
                email=user.email,
            )

            return user


def get_onboarding_service() -> OnboardingService:
    """
    Get onboarding service instance.

    Returns:
        OnboardingService instance
    """
    return OnboardingService()
