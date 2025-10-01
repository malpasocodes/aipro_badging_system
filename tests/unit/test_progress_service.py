"""Unit tests for ProgressService."""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlmodel import Session, create_engine, SQLModel

from app.models import (
    Award,
    AwardType,
    Program,
    Skill,
    MiniBadge,
    User,
    UserRole,
    Request,
    RequestStatus,
)
from app.services.progress_service import (
    ProgressService,
    get_progress_service,
    ProgressError,
    DuplicateAwardError,
)


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def progress_service(test_engine):
    """Create a ProgressService instance with test engine."""
    return ProgressService(engine=test_engine)


@pytest.fixture
def admin_user(test_engine):
    """Create an admin user."""
    user = User(
        id=uuid4(),
        google_sub="admin_test",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True,
    )
    with Session(test_engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@pytest.fixture
def student_user(test_engine):
    """Create a student user."""
    user = User(
        id=uuid4(),
        google_sub="student_test",
        email="student@test.com",
        role=UserRole.STUDENT,
        is_active=True,
    )
    with Session(test_engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@pytest.fixture
def program(test_engine):
    """Create a test program."""
    prog = Program(
        id=uuid4(),
        title="Test Program",
        description="Test Description",
        is_active=True,
        position=0,
    )
    with Session(test_engine) as session:
        session.add(prog)
        session.commit()
        session.refresh(prog)
    return prog


@pytest.fixture
def skill(test_engine, program):
    """Create a test skill."""
    sk = Skill(
        id=uuid4(),
        program_id=program.id,
        title="Test Skill",
        description="Test Description",
        is_active=True,
        position=0,
    )
    with Session(test_engine) as session:
        session.add(sk)
        session.commit()
        session.refresh(sk)
    return sk


@pytest.fixture
def mini_badges(test_engine, skill):
    """Create 3 test mini-badges under a skill."""
    badges = []
    for i in range(3):
        badge = MiniBadge(
            id=uuid4(),
            skill_id=skill.id,
            title=f"Mini-badge {i+1}",
            description=f"Description {i+1}",
            is_active=True,
            position=i,
        )
        badges.append(badge)

    with Session(test_engine) as session:
        for badge in badges:
            session.add(badge)
        session.commit()
        for badge in badges:
            session.refresh(badge)
    return badges


@pytest.fixture
def request_for_badge(test_engine, student_user, mini_badges):
    """Create an approved request for the first mini-badge."""
    req = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        badge_name=mini_badges[0].title,
        status=RequestStatus.APPROVED,
    )
    with Session(test_engine) as session:
        session.add(req)
        session.commit()
        session.refresh(req)
    return req


# Basic Award Creation Tests


def test_award_mini_badge_creates_record(
    progress_service, student_user, mini_badges, admin_user, request_for_badge
):
    """Test that awarding a mini-badge creates an award record."""
    awards = progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=request_for_badge.id,
        awarded_by=admin_user.id,
    )

    assert len(awards) >= 1
    mini_badge_award = awards[0]
    assert mini_badge_award.user_id == student_user.id
    assert mini_badge_award.award_type == AwardType.MINI_BADGE
    assert mini_badge_award.mini_badge_id == mini_badges[0].id
    assert mini_badge_award.request_id == request_for_badge.id
    assert mini_badge_award.awarded_by == admin_user.id
    assert mini_badge_award.awarded_at is not None


def test_award_mini_badge_duplicate_raises_error(
    progress_service, student_user, mini_badges, admin_user, request_for_badge
):
    """Test that awarding the same mini-badge twice raises DuplicateAwardError."""
    # Award first time
    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=request_for_badge.id,
        awarded_by=admin_user.id,
    )

    # Award second time should fail
    with pytest.raises(DuplicateAwardError):
        progress_service.award_mini_badge(
            user_id=student_user.id,
            mini_badge_id=mini_badges[0].id,
            request_id=request_for_badge.id,
            awarded_by=admin_user.id,
        )


def test_award_mini_badge_invalid_badge_raises_error(
    progress_service, student_user, admin_user, request_for_badge
):
    """Test that awarding a non-existent mini-badge raises ProgressError."""
    fake_badge_id = uuid4()

    with pytest.raises(ProgressError, match="not found"):
        progress_service.award_mini_badge(
            user_id=student_user.id,
            mini_badge_id=fake_badge_id,
            request_id=request_for_badge.id,
            awarded_by=admin_user.id,
        )


# Skill Progression Tests


def test_partial_skill_no_auto_award(
    progress_service, student_user, mini_badges, admin_user, test_engine
):
    """Test that partial skill completion doesn't auto-award skill."""
    # Create requests for testing
    req1 = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        badge_name=mini_badges[0].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req1)
        session.commit()
        session.refresh(req1)

    # Award only 1 of 3 mini-badges
    awards = progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=req1.id,
        awarded_by=admin_user.id,
    )

    # Should only have mini_badge award, not skill
    assert len(awards) == 1
    assert awards[0].award_type == AwardType.MINI_BADGE


def test_complete_skill_awards_skill_automatically(
    progress_service, student_user, mini_badges, admin_user, test_engine, program
):
    """Test that completing all mini-badges in a skill auto-awards the skill."""
    # Create a second skill in the program to prevent program award
    skill2 = Skill(
        id=uuid4(),
        program_id=program.id,
        title="Another Skill",
        is_active=True,
        position=1,
    )
    with Session(test_engine) as session:
        session.add(skill2)
        session.commit()
        session.refresh(skill2)

    # Create requests for all 3 mini-badges
    requests = []
    for badge in mini_badges:
        req = Request(
            id=uuid4(),
            user_id=student_user.id,
            mini_badge_id=badge.id,
            badge_name=badge.title,
            status=RequestStatus.APPROVED,
        )
        requests.append(req)

    with Session(test_engine) as session:
        for req in requests:
            session.add(req)
        session.commit()
        for req in requests:
            session.refresh(req)

    # Award first 2 mini-badges
    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=requests[0].id,
        awarded_by=admin_user.id,
    )

    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[1].id,
        request_id=requests[1].id,
        awarded_by=admin_user.id,
    )

    # Award third mini-badge - should trigger skill award but NOT program (need skill2 too)
    awards = progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[2].id,
        request_id=requests[2].id,
        awarded_by=admin_user.id,
    )

    # Should have both mini_badge and skill awards, NOT program
    assert len(awards) == 2
    assert awards[0].award_type == AwardType.MINI_BADGE
    assert awards[1].award_type == AwardType.SKILL
    assert awards[1].skill_id == mini_badges[0].skill_id
    assert awards[1].awarded_by is None  # Automatic award


def test_check_skill_completion_partial(
    progress_service, student_user, mini_badges, admin_user, skill, test_engine
):
    """Test checking skill completion when partially complete."""
    # Award 1 of 3 mini-badges
    req = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        badge_name=mini_badges[0].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req)
        session.commit()
        session.refresh(req)

    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=req.id,
        awarded_by=admin_user.id,
    )

    # Check should return False
    is_complete = progress_service.check_skill_completion(student_user.id, skill.id)
    assert is_complete is False


def test_check_skill_completion_complete(
    progress_service, student_user, mini_badges, admin_user, skill, test_engine
):
    """Test checking skill completion when fully complete."""
    # Award all 3 mini-badges
    for badge in mini_badges:
        req = Request(
            id=uuid4(),
            user_id=student_user.id,
            mini_badge_id=badge.id,
            badge_name=badge.title,
            status=RequestStatus.APPROVED,
        )

        with Session(test_engine) as session:
            session.add(req)
            session.commit()
            session.refresh(req)

        progress_service.award_mini_badge(
            user_id=student_user.id,
            mini_badge_id=badge.id,
            request_id=req.id,
            awarded_by=admin_user.id,
        )

    # Check should return True
    is_complete = progress_service.check_skill_completion(student_user.id, skill.id)
    assert is_complete is True


# Program Progression Tests


def test_complete_program_awards_program_automatically(
    progress_service, test_engine, student_user, program, admin_user
):
    """Test that completing all skills in a program auto-awards the program."""
    # Create 2 skills under program
    skills = []
    for i in range(2):
        skill = Skill(
            id=uuid4(),
            program_id=program.id,
            title=f"Skill {i+1}",
            description=f"Description {i+1}",
            is_active=True,
            position=i,
        )
        skills.append(skill)

    with Session(test_engine) as session:
        for skill in skills:
            session.add(skill)
        session.commit()
        for skill in skills:
            session.refresh(skill)

    # Create mini-badges for each skill (1 per skill for simplicity)
    all_badges = []
    for skill in skills:
        badge = MiniBadge(
            id=uuid4(),
            skill_id=skill.id,
            title=f"Badge for {skill.title}",
            description="Description",
            is_active=True,
            position=0,
        )
        all_badges.append(badge)

    with Session(test_engine) as session:
        for badge in all_badges:
            session.add(badge)
        session.commit()
        for badge in all_badges:
            session.refresh(badge)

    # Award first mini-badge (completes first skill)
    req1 = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=all_badges[0].id,
        badge_name=all_badges[0].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req1)
        session.commit()
        session.refresh(req1)

    awards1 = progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=all_badges[0].id,
        request_id=req1.id,
        awarded_by=admin_user.id,
    )

    # Should have mini_badge and skill
    assert len(awards1) == 2

    # Award second mini-badge (completes second skill and program)
    req2 = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=all_badges[1].id,
        badge_name=all_badges[1].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req2)
        session.commit()
        session.refresh(req2)

    awards2 = progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=all_badges[1].id,
        request_id=req2.id,
        awarded_by=admin_user.id,
    )

    # Should have mini_badge, skill, and program
    assert len(awards2) == 3
    assert awards2[0].award_type == AwardType.MINI_BADGE
    assert awards2[1].award_type == AwardType.SKILL
    assert awards2[2].award_type == AwardType.PROGRAM
    assert awards2[2].program_id == program.id
    assert awards2[2].awarded_by is None  # Automatic


def test_check_program_completion_partial(
    progress_service, test_engine, student_user, program, admin_user
):
    """Test checking program completion when partially complete."""
    # Create 2 skills, award only 1
    skills = []
    for i in range(2):
        skill = Skill(
            id=uuid4(),
            program_id=program.id,
            title=f"Skill {i+1}",
            is_active=True,
            position=i,
        )
        skills.append(skill)

    with Session(test_engine) as session:
        for skill in skills:
            session.add(skill)
        session.commit()
        for skill in skills:
            session.refresh(skill)

    # Award only first skill manually
    progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skills[0].id,
        awarded_by=admin_user.id,
    )

    # Check should return False
    is_complete = progress_service.check_program_completion(student_user.id, program.id)
    assert is_complete is False


def test_check_program_completion_complete(
    progress_service, test_engine, student_user, program, admin_user
):
    """Test checking program completion when fully complete."""
    # Create 2 skills, award both
    skills = []
    for i in range(2):
        skill = Skill(
            id=uuid4(),
            program_id=program.id,
            title=f"Skill {i+1}",
            is_active=True,
            position=i,
        )
        skills.append(skill)

    with Session(test_engine) as session:
        for skill in skills:
            session.add(skill)
        session.commit()
        for skill in skills:
            session.refresh(skill)

    # Award both skills
    for skill in skills:
        progress_service.award_skill(
            user_id=student_user.id,
            skill_id=skill.id,
            awarded_by=admin_user.id,
        )

    # Check should return True
    is_complete = progress_service.check_program_completion(student_user.id, program.id)
    assert is_complete is True


# Manual Award Tests


def test_manual_skill_award(progress_service, student_user, skill, admin_user):
    """Test manually awarding a skill."""
    award = progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skill.id,
        awarded_by=admin_user.id,
        reason="Manual award for testing",
    )

    assert award.user_id == student_user.id
    assert award.award_type == AwardType.SKILL
    assert award.skill_id == skill.id
    assert award.awarded_by == admin_user.id
    assert award.notes == "Manual award for testing"


def test_manual_program_award(progress_service, student_user, program, admin_user):
    """Test manually awarding a program."""
    award = progress_service.award_program(
        user_id=student_user.id,
        program_id=program.id,
        awarded_by=admin_user.id,
        reason="Manual award for testing",
    )

    assert award.user_id == student_user.id
    assert award.award_type == AwardType.PROGRAM
    assert award.program_id == program.id
    assert award.awarded_by == admin_user.id
    assert award.notes == "Manual award for testing"


# Progress Query Tests


def test_get_user_awards_empty(progress_service, student_user):
    """Test getting awards for user with no awards."""
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 0


def test_get_user_awards_multiple_types(
    progress_service, student_user, mini_badges, skill, program, admin_user, test_engine
):
    """Test getting awards with multiple types."""
    # Create a mini-badge award
    req = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        badge_name=mini_badges[0].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req)
        session.commit()
        session.refresh(req)

    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=req.id,
        awarded_by=admin_user.id,
    )

    # Manually award skill and program
    progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skill.id,
        awarded_by=admin_user.id,
    )

    progress_service.award_program(
        user_id=student_user.id,
        program_id=program.id,
        awarded_by=admin_user.id,
    )

    # Get all awards
    all_awards = progress_service.get_user_awards(student_user.id)
    assert len(all_awards) == 3

    # Get filtered by type
    mini_badge_awards = progress_service.get_user_awards(
        student_user.id, award_type=AwardType.MINI_BADGE
    )
    assert len(mini_badge_awards) == 1

    skill_awards = progress_service.get_user_awards(
        student_user.id, award_type=AwardType.SKILL
    )
    assert len(skill_awards) == 1

    program_awards = progress_service.get_user_awards(
        student_user.id, award_type=AwardType.PROGRAM
    )
    assert len(program_awards) == 1


def test_get_skill_progress_no_awards(progress_service, student_user, skill, mini_badges):
    """Test getting skill progress with no awards."""
    progress = progress_service.get_skill_progress(student_user.id, skill.id)

    assert progress["skill_id"] == str(skill.id)
    assert progress["skill_title"] == skill.title
    assert progress["earned_count"] == 0
    assert progress["total_count"] == 3
    assert progress["percentage"] == 0
    assert len(progress["mini_badges"]) == 3
    assert all(not mb["earned"] for mb in progress["mini_badges"])


def test_get_skill_progress_partial(
    progress_service, student_user, skill, mini_badges, admin_user, test_engine
):
    """Test getting skill progress with partial completion."""
    # Award 1 of 3 mini-badges
    req = Request(
        id=uuid4(),
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        badge_name=mini_badges[0].title,
        status=RequestStatus.APPROVED,
    )

    with Session(test_engine) as session:
        session.add(req)
        session.commit()
        session.refresh(req)

    progress_service.award_mini_badge(
        user_id=student_user.id,
        mini_badge_id=mini_badges[0].id,
        request_id=req.id,
        awarded_by=admin_user.id,
    )

    progress = progress_service.get_skill_progress(student_user.id, skill.id)

    assert progress["earned_count"] == 1
    assert progress["total_count"] == 3
    assert progress["percentage"] == 33
    assert progress["mini_badges"][0]["earned"] is True
    assert progress["mini_badges"][1]["earned"] is False


def test_get_skill_progress_complete(
    progress_service, student_user, skill, mini_badges, admin_user, test_engine
):
    """Test getting skill progress when fully complete."""
    # Award all 3 mini-badges
    for badge in mini_badges:
        req = Request(
            id=uuid4(),
            user_id=student_user.id,
            mini_badge_id=badge.id,
            badge_name=badge.title,
            status=RequestStatus.APPROVED,
        )

        with Session(test_engine) as session:
            session.add(req)
            session.commit()
            session.refresh(req)

        progress_service.award_mini_badge(
            user_id=student_user.id,
            mini_badge_id=badge.id,
            request_id=req.id,
            awarded_by=admin_user.id,
        )

    progress = progress_service.get_skill_progress(student_user.id, skill.id)

    assert progress["earned_count"] == 3
    assert progress["total_count"] == 3
    assert progress["percentage"] == 100
    assert all(mb["earned"] for mb in progress["mini_badges"])


def test_get_program_progress(progress_service, test_engine, student_user, program, admin_user):
    """Test getting program progress."""
    # Create 2 skills
    skills = []
    for i in range(2):
        skill = Skill(
            id=uuid4(),
            program_id=program.id,
            title=f"Skill {i+1}",
            is_active=True,
            position=i,
        )
        skills.append(skill)

    with Session(test_engine) as session:
        for skill in skills:
            session.add(skill)
        session.commit()
        for skill in skills:
            session.refresh(skill)

    # Award 1 of 2 skills
    progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skills[0].id,
        awarded_by=admin_user.id,
    )

    progress = progress_service.get_program_progress(student_user.id, program.id)

    assert progress["program_id"] == str(program.id)
    assert progress["program_title"] == program.title
    assert progress["earned_skills"] == 1
    assert progress["total_skills"] == 2
    assert progress["percentage"] == 50


# Inactive Badge Tests


def test_inactive_mini_badge_not_counted_in_skill_completion(
    progress_service, test_engine, student_user, skill, admin_user, program
):
    """Test that inactive mini-badges don't count toward skill completion."""
    # Create a second skill in the program to prevent program award
    skill2 = Skill(
        id=uuid4(),
        program_id=program.id,
        title="Another Skill",
        is_active=True,
        position=1,
    )
    with Session(test_engine) as session:
        session.add(skill2)
        session.commit()
        session.refresh(skill2)

    # Create 3 mini-badges, mark one as inactive
    badges = []
    for i in range(3):
        badge = MiniBadge(
            id=uuid4(),
            skill_id=skill.id,
            title=f"Badge {i+1}",
            is_active=(i != 2),  # Third badge inactive
            position=i,
        )
        badges.append(badge)

    with Session(test_engine) as session:
        for badge in badges:
            session.add(badge)
        session.commit()
        for badge in badges:
            session.refresh(badge)

    # Award only the 2 active badges
    for badge in badges[:2]:
        req = Request(
            id=uuid4(),
            user_id=student_user.id,
            mini_badge_id=badge.id,
            badge_name=badge.title,
            status=RequestStatus.APPROVED,
        )

        with Session(test_engine) as session:
            session.add(req)
            session.commit()
            session.refresh(req)

        awards = progress_service.award_mini_badge(
            user_id=student_user.id,
            mini_badge_id=badge.id,
            request_id=req.id,
            awarded_by=admin_user.id,
        )

        # Last badge should trigger skill award (only 2 active badges required)
        # Should NOT trigger program award (need skill2 too)
        if badge == badges[1]:
            assert len(awards) == 2  # mini_badge + skill, NOT program
            assert awards[1].award_type == AwardType.SKILL


# Factory Function Test


def test_get_progress_service_factory():
    """Test the progress service factory function."""
    service = get_progress_service()
    assert isinstance(service, ProgressService)
    assert service.engine is None

    # With engine
    engine = create_engine("sqlite:///:memory:")
    service_with_engine = get_progress_service(engine=engine)
    assert service_with_engine.engine == engine
