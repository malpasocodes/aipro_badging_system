"""Unit tests for OnboardingService."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.core.database import get_engine
from app.models.user import User, UserRole
from app.services.onboarding import (
    OnboardingService,
    OnboardingError,
    ValidationError,
    get_onboarding_service,
)


@pytest.fixture
def onboarding_service():
    """Create OnboardingService instance."""
    return OnboardingService()


@pytest.fixture
def test_user():
    """Create a test user in the database."""
    engine = get_engine()
    with Session(engine) as session:
        user = User(
            google_sub="test_google_sub_" + str(uuid4()),
            email=f"test_{uuid4()}@example.com",
            role=UserRole.STUDENT,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    yield user_id

    # Cleanup
    with Session(engine) as session:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        if user:
            session.delete(user)
            session.commit()


class TestUsernameValidation:
    """Test username validation."""

    def test_validate_username_valid(self, onboarding_service):
        """Test valid username passes validation."""
        # Should not raise
        onboarding_service._validate_username("valid_user-123")
        onboarding_service._validate_username("abc")
        onboarding_service._validate_username("a" * 50)

    def test_validate_username_too_short(self, onboarding_service):
        """Test username < 3 characters fails."""
        with pytest.raises(ValidationError, match="at least 3 characters"):
            onboarding_service._validate_username("ab")

    def test_validate_username_too_long(self, onboarding_service):
        """Test username > 50 characters fails."""
        with pytest.raises(ValidationError, match="not exceed 50 characters"):
            onboarding_service._validate_username("a" * 51)

    def test_validate_username_invalid_chars(self, onboarding_service):
        """Test username with invalid characters fails."""
        with pytest.raises(ValidationError, match="letters, numbers, underscores"):
            onboarding_service._validate_username("user@name")
        with pytest.raises(ValidationError, match="letters, numbers, underscores"):
            onboarding_service._validate_username("user name")
        with pytest.raises(ValidationError, match="letters, numbers, underscores"):
            onboarding_service._validate_username("user.name")

    def test_validate_username_leading_trailing_special(self, onboarding_service):
        """Test username cannot start/end with underscore or hyphen."""
        with pytest.raises(ValidationError, match="cannot start or end"):
            onboarding_service._validate_username("_username")
        with pytest.raises(ValidationError, match="cannot start or end"):
            onboarding_service._validate_username("username_")
        with pytest.raises(ValidationError, match="cannot start or end"):
            onboarding_service._validate_username("-username")
        with pytest.raises(ValidationError, match="cannot start or end"):
            onboarding_service._validate_username("username-")

    def test_validate_username_whitespace(self, onboarding_service):
        """Test username with whitespace is stripped and validated."""
        # Valid after stripping
        onboarding_service._validate_username("  valid_user  ")

        # Too short after stripping
        with pytest.raises(ValidationError, match="at least 3 characters"):
            onboarding_service._validate_username("  ab  ")

    def test_validate_username_empty(self, onboarding_service):
        """Test empty username fails."""
        with pytest.raises(ValidationError, match="required"):
            onboarding_service._validate_username("")
        with pytest.raises(ValidationError, match="required"):
            onboarding_service._validate_username("   ")


class TestEmailValidation:
    """Test email validation."""

    def test_validate_email_valid(self, onboarding_service):
        """Test valid email passes validation."""
        # Should not raise
        onboarding_service._validate_email("user@example.com")
        onboarding_service._validate_email("user.name@example.com")
        onboarding_service._validate_email("user+tag@example.co.uk")
        onboarding_service._validate_email("user_123@sub.example.com")

    def test_validate_email_invalid(self, onboarding_service):
        """Test invalid email fails validation."""
        with pytest.raises(ValidationError, match="not a valid email"):
            onboarding_service._validate_email("not-an-email")
        with pytest.raises(ValidationError, match="not a valid email"):
            onboarding_service._validate_email("@example.com")
        with pytest.raises(ValidationError, match="not a valid email"):
            onboarding_service._validate_email("user@")
        with pytest.raises(ValidationError, match="not a valid email"):
            onboarding_service._validate_email("user@@example.com")

    def test_validate_email_too_long(self, onboarding_service):
        """Test email exceeding length limit fails."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError, match="too long"):
            onboarding_service._validate_email(long_email)

    def test_validate_email_local_too_long(self, onboarding_service):
        """Test email with local part > 64 chars fails."""
        long_local = "a" * 65 + "@example.com"
        with pytest.raises(ValidationError, match="local part is too long"):
            onboarding_service._validate_email(long_local)

    def test_validate_email_empty(self, onboarding_service):
        """Test empty email fails."""
        with pytest.raises(ValidationError, match="required"):
            onboarding_service._validate_email("")
        with pytest.raises(ValidationError, match="required"):
            onboarding_service._validate_email("   ")

    def test_validate_email_whitespace(self, onboarding_service):
        """Test email with whitespace is stripped and validated."""
        # Valid after stripping
        onboarding_service._validate_email("  user@example.com  ")

    def test_validate_email_custom_field_name(self, onboarding_service):
        """Test custom field name appears in error messages."""
        with pytest.raises(ValidationError, match="Substack email is required"):
            onboarding_service._validate_email("", "Substack email")


class TestCompleteOnboarding:
    """Test complete_onboarding method."""

    def test_complete_onboarding_success(self, onboarding_service, test_user):
        """Test successful onboarding completion."""
        user = onboarding_service.complete_onboarding(
            user_id=test_user,
            username="test_user",
            substack_email="substack@example.com",
            meetup_email="meetup@example.com",
        )

        assert user.username == "test_user"
        assert user.substack_email == "substack@example.com"
        assert user.meetup_email == "meetup@example.com"
        assert user.onboarding_completed_at is not None
        assert isinstance(user.onboarding_completed_at, datetime)
        assert user.is_onboarded() is True

    def test_complete_onboarding_strips_whitespace(self, onboarding_service, test_user):
        """Test onboarding strips whitespace from inputs."""
        user = onboarding_service.complete_onboarding(
            user_id=test_user,
            username="  test_user  ",
            substack_email="  substack@example.com  ",
            meetup_email="  meetup@example.com  ",
        )

        assert user.username == "test_user"
        assert user.substack_email == "substack@example.com"
        assert user.meetup_email == "meetup@example.com"

    def test_complete_onboarding_lowercases_emails(self, onboarding_service, test_user):
        """Test onboarding lowercases email addresses."""
        user = onboarding_service.complete_onboarding(
            user_id=test_user,
            username="test_user",
            substack_email="SubStack@Example.COM",
            meetup_email="MeetUp@Example.COM",
        )

        assert user.substack_email == "substack@example.com"
        assert user.meetup_email == "meetup@example.com"

    def test_complete_onboarding_already_onboarded(self, onboarding_service, test_user):
        """Test onboarding when user already onboarded returns existing user."""
        # First onboarding
        onboarding_service.complete_onboarding(
            user_id=test_user,
            username="original_user",
            substack_email="original@example.com",
            meetup_email="original@example.com",
        )

        # Second onboarding attempt
        user = onboarding_service.complete_onboarding(
            user_id=test_user,
            username="new_user",
            substack_email="new@example.com",
            meetup_email="new@example.com",
        )

        # Should keep original data
        assert user.username == "original_user"
        assert user.substack_email == "original@example.com"

    def test_complete_onboarding_invalid_username(self, onboarding_service, test_user):
        """Test onboarding fails with invalid username."""
        with pytest.raises(ValidationError, match="at least 3 characters"):
            onboarding_service.complete_onboarding(
                user_id=test_user,
                username="ab",
                substack_email="substack@example.com",
                meetup_email="meetup@example.com",
            )

    def test_complete_onboarding_invalid_substack_email(
        self, onboarding_service, test_user
    ):
        """Test onboarding fails with invalid Substack email."""
        with pytest.raises(ValidationError, match="Substack email"):
            onboarding_service.complete_onboarding(
                user_id=test_user,
                username="test_user",
                substack_email="not-an-email",
                meetup_email="meetup@example.com",
            )

    def test_complete_onboarding_invalid_meetup_email(
        self, onboarding_service, test_user
    ):
        """Test onboarding fails with invalid Meetup email."""
        with pytest.raises(ValidationError, match="Meetup email"):
            onboarding_service.complete_onboarding(
                user_id=test_user,
                username="test_user",
                substack_email="substack@example.com",
                meetup_email="not-an-email",
            )

    def test_complete_onboarding_user_not_found(self, onboarding_service):
        """Test onboarding fails for non-existent user."""
        fake_user_id = uuid4()
        with pytest.raises(OnboardingError, match="User not found"):
            onboarding_service.complete_onboarding(
                user_id=fake_user_id,
                username="test_user",
                substack_email="substack@example.com",
                meetup_email="meetup@example.com",
            )


class TestUpdateOnboardingInfo:
    """Test update_onboarding_info method."""

    @pytest.fixture
    def onboarded_user(self, onboarding_service):
        """Create a user that has completed onboarding."""
        engine = get_engine()
        with Session(engine) as session:
            user = User(
                google_sub="onboarded_" + str(uuid4()),
                email=f"onboarded_{uuid4()}@example.com",
                role=UserRole.STUDENT,
                username="original_user",
                substack_email="original@example.com",
                meetup_email="original@example.com",
                onboarding_completed_at=datetime.utcnow(),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        yield user_id

        # Cleanup
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            if user:
                session.delete(user)
                session.commit()

    def test_update_username(self, onboarding_service, onboarded_user):
        """Test updating only username."""
        user = onboarding_service.update_onboarding_info(
            user_id=onboarded_user, username="new_username"
        )

        assert user.username == "new_username"
        assert user.substack_email == "original@example.com"
        assert user.meetup_email == "original@example.com"

    def test_update_substack_email(self, onboarding_service, onboarded_user):
        """Test updating only Substack email."""
        user = onboarding_service.update_onboarding_info(
            user_id=onboarded_user, substack_email="new_substack@example.com"
        )

        assert user.username == "original_user"
        assert user.substack_email == "new_substack@example.com"
        assert user.meetup_email == "original@example.com"

    def test_update_meetup_email(self, onboarding_service, onboarded_user):
        """Test updating only Meetup email."""
        user = onboarding_service.update_onboarding_info(
            user_id=onboarded_user, meetup_email="new_meetup@example.com"
        )

        assert user.username == "original_user"
        assert user.substack_email == "original@example.com"
        assert user.meetup_email == "new_meetup@example.com"

    def test_update_multiple_fields(self, onboarding_service, onboarded_user):
        """Test updating multiple fields at once."""
        user = onboarding_service.update_onboarding_info(
            user_id=onboarded_user,
            username="new_username",
            substack_email="new_substack@example.com",
        )

        assert user.username == "new_username"
        assert user.substack_email == "new_substack@example.com"
        assert user.meetup_email == "original@example.com"

    def test_update_not_onboarded_user(self, onboarding_service, test_user):
        """Test update fails for user who hasn't completed onboarding."""
        with pytest.raises(OnboardingError, match="not completed onboarding"):
            onboarding_service.update_onboarding_info(
                user_id=test_user, username="new_username"
            )

    def test_update_invalid_username(self, onboarding_service, onboarded_user):
        """Test update fails with invalid username."""
        with pytest.raises(ValidationError, match="at least 3 characters"):
            onboarding_service.update_onboarding_info(
                user_id=onboarded_user, username="ab"
            )

    def test_update_user_not_found(self, onboarding_service):
        """Test update fails for non-existent user."""
        fake_user_id = uuid4()
        with pytest.raises(OnboardingError, match="User not found"):
            onboarding_service.update_onboarding_info(
                user_id=fake_user_id, username="new_username"
            )


class TestCheckOnboardingStatus:
    """Test check_onboarding_status method."""

    def test_check_onboarding_status_true(self, onboarding_service):
        """Test user with all fields is onboarded."""
        user = User(
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT,
            username="test_user",
            substack_email="substack@example.com",
            meetup_email="meetup@example.com",
            onboarding_completed_at=datetime.utcnow(),
        )

        assert onboarding_service.check_onboarding_status(user) is True
        assert user.is_onboarded() is True

    def test_check_onboarding_status_false_no_username(self, onboarding_service):
        """Test user without username is not onboarded."""
        user = User(
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT,
            username=None,
            substack_email="substack@example.com",
            meetup_email="meetup@example.com",
            onboarding_completed_at=datetime.utcnow(),
        )

        assert onboarding_service.check_onboarding_status(user) is False
        assert user.is_onboarded() is False

    def test_check_onboarding_status_false_no_timestamp(self, onboarding_service):
        """Test user without timestamp is not onboarded."""
        user = User(
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT,
            username="test_user",
            substack_email="substack@example.com",
            meetup_email="meetup@example.com",
            onboarding_completed_at=None,
        )

        assert onboarding_service.check_onboarding_status(user) is False
        assert user.is_onboarded() is False

    def test_check_onboarding_status_false_partial(self, onboarding_service):
        """Test user with partial onboarding is not onboarded."""
        user = User(
            google_sub="test_sub",
            email="test@example.com",
            role=UserRole.STUDENT,
            username="test_user",
            substack_email=None,
            meetup_email=None,
            onboarding_completed_at=None,
        )

        assert onboarding_service.check_onboarding_status(user) is False
        assert user.is_onboarded() is False


class TestGetOnboardingService:
    """Test get_onboarding_service factory function."""

    def test_get_onboarding_service(self):
        """Test factory function returns OnboardingService instance."""
        service = get_onboarding_service()
        assert isinstance(service, OnboardingService)
