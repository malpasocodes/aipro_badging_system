"""Integration tests for onboarding flow."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.core.database import get_engine
from app.models.user import User, UserRole
from app.services.onboarding import (
    OnboardingError,
    ValidationError,
    get_onboarding_service,
)


@pytest.fixture
def clean_database():
    """Clean up test users before and after tests."""
    engine = get_engine()
    test_emails = []

    yield test_emails

    # Cleanup after test
    with Session(engine) as session:
        for email in test_emails:
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()
            if user:
                session.delete(user)
        session.commit()


class TestNewUserOnboardingFlow:
    """Test complete onboarding flow for new users."""

    def test_new_user_onboarding_flow(self, clean_database):
        """Test complete onboarding flow for a new user."""
        engine = get_engine()
        test_email = f"new_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Step 1: Create a new authenticated user (simulating OAuth)
        with Session(engine) as session:
            user = User(
                google_sub="new_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Step 2: Check onboarding status (should be False)
        onboarding_service = get_onboarding_service()
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert not onboarding_service.check_onboarding_status(user)
            assert not user.is_onboarded()

        # Step 3: Complete onboarding
        updated_user = onboarding_service.complete_onboarding(
            user_id=user_id,
            username="new_test_user",
            substack_email="substack@example.com",
            meetup_email="meetup@example.com",
        )

        # Step 4: Verify onboarding completed
        assert updated_user.username == "new_test_user"
        assert updated_user.substack_email == "substack@example.com"
        assert updated_user.meetup_email == "meetup@example.com"
        assert updated_user.onboarding_completed_at is not None
        assert updated_user.is_onboarded()

        # Step 5: Verify data persists
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            persisted_user = session.exec(statement).first()
            assert persisted_user is not None
            assert persisted_user.username == "new_test_user"
            assert persisted_user.substack_email == "substack@example.com"
            assert persisted_user.meetup_email == "meetup@example.com"
            assert persisted_user.onboarding_completed_at is not None
            assert onboarding_service.check_onboarding_status(persisted_user)

    def test_existing_user_not_onboarded(self, clean_database):
        """Test existing user without onboarding is prompted."""
        engine = get_engine()
        test_email = f"existing_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user without onboarding data
        with Session(engine) as session:
            user = User(
                google_sub="existing_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
                username=None,
                substack_email=None,
                meetup_email=None,
                onboarding_completed_at=None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Check onboarding status
        onboarding_service = get_onboarding_service()
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert not onboarding_service.check_onboarding_status(user)
            assert not user.is_onboarded()

    def test_onboarded_user_bypasses_form(self, clean_database):
        """Test onboarded user goes directly to app."""
        engine = get_engine()
        test_email = f"onboarded_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user with complete onboarding data
        with Session(engine) as session:
            user = User(
                google_sub="onboarded_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
                username="onboarded_user",
                substack_email="substack@example.com",
                meetup_email="meetup@example.com",
                onboarding_completed_at=datetime.utcnow(),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Check onboarding status
        onboarding_service = get_onboarding_service()
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert onboarding_service.check_onboarding_status(user)
            assert user.is_onboarded()

    def test_onboarding_data_persists_across_sessions(self, clean_database):
        """Test onboarding data persists correctly in database."""
        engine = get_engine()
        test_email = f"persist_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user
        with Session(engine) as session:
            user = User(
                google_sub="persist_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Complete onboarding in first session
        onboarding_service = get_onboarding_service()
        onboarding_service.complete_onboarding(
            user_id=user_id,
            username="persist_user",
            substack_email="persist_substack@example.com",
            meetup_email="persist_meetup@example.com",
        )

        # Retrieve user in new session
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert user.username == "persist_user"
            assert user.substack_email == "persist_substack@example.com"
            assert user.meetup_email == "persist_meetup@example.com"
            assert user.onboarding_completed_at is not None

        # Retrieve again in another session
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert user.is_onboarded()


class TestOnboardingUpdateFlow:
    """Test updating onboarding information."""

    def test_update_onboarding_info_flow(self, clean_database):
        """Test updating onboarding information for an onboarded user."""
        engine = get_engine()
        test_email = f"update_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create and onboard user
        with Session(engine) as session:
            user = User(
                google_sub="update_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        onboarding_service = get_onboarding_service()
        onboarding_service.complete_onboarding(
            user_id=user_id,
            username="original_username",
            substack_email="original_substack@example.com",
            meetup_email="original_meetup@example.com",
        )

        # Update username
        updated_user = onboarding_service.update_onboarding_info(
            user_id=user_id, username="new_username"
        )
        assert updated_user.username == "new_username"
        assert updated_user.substack_email == "original_substack@example.com"
        assert updated_user.meetup_email == "original_meetup@example.com"

        # Update both emails
        updated_user = onboarding_service.update_onboarding_info(
            user_id=user_id,
            substack_email="new_substack@example.com",
            meetup_email="new_meetup@example.com",
        )
        assert updated_user.username == "new_username"
        assert updated_user.substack_email == "new_substack@example.com"
        assert updated_user.meetup_email == "new_meetup@example.com"

    def test_update_not_onboarded_user_fails(self, clean_database):
        """Test updating onboarding info fails for user who hasn't onboarded."""
        engine = get_engine()
        test_email = f"not_onboarded_update_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user without onboarding
        with Session(engine) as session:
            user = User(
                google_sub="not_onboarded_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Try to update (should fail)
        onboarding_service = get_onboarding_service()
        with pytest.raises(OnboardingError, match="not completed onboarding"):
            onboarding_service.update_onboarding_info(
                user_id=user_id, username="new_username"
            )


class TestOnboardingValidationIntegration:
    """Test validation in integration context."""

    def test_onboarding_rejects_invalid_data(self, clean_database):
        """Test onboarding rejects invalid data at service boundary."""
        engine = get_engine()
        test_email = f"invalid_data_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user
        with Session(engine) as session:
            user = User(
                google_sub="invalid_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        onboarding_service = get_onboarding_service()

        # Try with invalid username (too short)
        with pytest.raises(ValidationError, match="at least 3 characters"):
            onboarding_service.complete_onboarding(
                user_id=user_id,
                username="ab",
                substack_email="valid@example.com",
                meetup_email="valid@example.com",
            )

        # Try with invalid email
        with pytest.raises(ValidationError, match="Substack email"):
            onboarding_service.complete_onboarding(
                user_id=user_id,
                username="valid_user",
                substack_email="not-an-email",
                meetup_email="valid@example.com",
            )

        # Verify user remains not onboarded after failed attempts
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert not user.is_onboarded()

    def test_onboarding_with_whitespace_normalization(self, clean_database):
        """Test onboarding normalizes whitespace and email case."""
        engine = get_engine()
        test_email = f"whitespace_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user
        with Session(engine) as session:
            user = User(
                google_sub="whitespace_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Complete onboarding with whitespace and mixed case
        onboarding_service = get_onboarding_service()
        updated_user = onboarding_service.complete_onboarding(
            user_id=user_id,
            username="  test_user  ",
            substack_email="  SubStack@Example.COM  ",
            meetup_email="  MeetUp@Example.COM  ",
        )

        # Verify normalization
        assert updated_user.username == "test_user"
        assert updated_user.substack_email == "substack@example.com"
        assert updated_user.meetup_email == "meetup@example.com"

        # Verify persisted data
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            assert user is not None
            assert user.username == "test_user"
            assert user.substack_email == "substack@example.com"
            assert user.meetup_email == "meetup@example.com"


class TestOnboardingIdempotency:
    """Test onboarding idempotency."""

    def test_onboarding_twice_keeps_original_data(self, clean_database):
        """Test completing onboarding twice keeps original data."""
        engine = get_engine()
        test_email = f"idempotent_user_{uuid4()}@example.com"
        clean_database.append(test_email)

        # Create user
        with Session(engine) as session:
            user = User(
                google_sub="idempotent_google_sub_" + str(uuid4()),
                email=test_email,
                role=UserRole.STUDENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        onboarding_service = get_onboarding_service()

        # First onboarding
        first_result = onboarding_service.complete_onboarding(
            user_id=user_id,
            username="first_username",
            substack_email="first@example.com",
            meetup_email="first@example.com",
        )
        first_timestamp = first_result.onboarding_completed_at

        # Second onboarding attempt
        second_result = onboarding_service.complete_onboarding(
            user_id=user_id,
            username="second_username",
            substack_email="second@example.com",
            meetup_email="second@example.com",
        )

        # Should keep original data
        assert second_result.username == "first_username"
        assert second_result.substack_email == "first@example.com"
        assert second_result.meetup_email == "first@example.com"
        assert second_result.onboarding_completed_at == first_timestamp
