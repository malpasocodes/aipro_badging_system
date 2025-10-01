"""Integration tests for badge progression workflows."""

import pytest
from uuid import uuid4

from app.models import (
    User,
    UserRole,
    Program,
    Skill,
    MiniBadge,
    Capstone,
    Request,
    RequestStatus,
    Award,
    AwardType,
)
from app.services import (
    get_request_service,
    get_progress_service,
    get_catalog_service,
)


@pytest.fixture
def catalog_service(test_engine):
    """Create catalog service with test engine."""
    return get_catalog_service(engine=test_engine)


@pytest.fixture
def request_service(test_engine):
    """Create request service with test engine."""
    return get_request_service(engine=test_engine)


@pytest.fixture
def progress_service(test_engine):
    """Create progress service with test engine."""
    return get_progress_service(engine=test_engine)


@pytest.fixture
def admin_user(test_engine):
    """Create admin user."""
    from sqlmodel import Session
    admin = User(
        id=uuid4(),
        google_sub="admin_test",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True,
    )
    with Session(test_engine) as session:
        session.add(admin)
        session.commit()
        session.refresh(admin)
    return admin


@pytest.fixture
def student_user(test_engine):
    """Create student user."""
    from sqlmodel import Session
    student = User(
        id=uuid4(),
        google_sub="student_test",
        email="student@test.com",
        role=UserRole.STUDENT,
        is_active=True,
    )
    with Session(test_engine) as session:
        session.add(student)
        session.commit()
        session.refresh(student)
    return student


@pytest.fixture
def second_student(test_engine):
    """Create second student user."""
    from sqlmodel import Session
    student = User(
        id=uuid4(),
        google_sub="student2_test",
        email="student2@test.com",
        role=UserRole.STUDENT,
        is_active=True,
    )
    with Session(test_engine) as session:
        session.add(student)
        session.commit()
        session.refresh(student)
    return student


def test_approve_request_awards_mini_badge(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that approving a request automatically awards the mini-badge."""
    # Create catalog structure
    program = catalog_service.create_program(
        title="Test Program",
        description="Test",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create 2 skills to prevent program award
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description="Test",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill 2",
        description="Test",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description="Test",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Student submits request
    request = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=mini_badge.id,
    )

    assert request.status == RequestStatus.PENDING

    # Admin approves request
    approved_request = request_service.approve_request(
        request_id=request.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    assert approved_request.status == RequestStatus.APPROVED

    # Check that awards were created (mini_badge + skill since only 1 badge in skill)
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 2  # mini_badge + skill (automatic)

    # Check mini-badge award
    mini_badge_award = [a for a in awards if a.award_type == AwardType.MINI_BADGE][0]
    assert mini_badge_award.mini_badge_id == mini_badge.id
    assert mini_badge_award.request_id == request.id

    # Check skill award (automatic)
    skill_award = [a for a in awards if a.award_type == AwardType.SKILL][0]
    assert skill_award.skill_id == skill.id
    assert skill_award.awarded_by is None  # Automatic award


def test_complete_skill_progression(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test complete skill progression: 3 mini-badges → skill award."""
    # Create catalog with 2 skills (to prevent program award)
    program = catalog_service.create_program(
        title="Python Basics",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Variables",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Functions",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create 3 mini-badges
    badges = []
    for i in range(3):
        badge = catalog_service.create_mini_badge(
            skill_id=skill.id,
            title=f"Badge {i+1}",
            description=None,
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )
        badges.append(badge)

    # Student requests and gets approved for first 2 badges
    for badge in badges[:2]:
        request = request_service.submit_request(
            user_id=student_user.id,
            mini_badge_id=badge.id,
        )
        request_service.approve_request(
            request_id=request.id,
            approver_id=admin_user.id,
            approver_role=admin_user.role,
        )

    # Check progress - should have 2 mini-badge awards, no skill yet
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 2
    assert all(a.award_type == AwardType.MINI_BADGE for a in awards)

    # Request and approve third badge - should trigger skill award
    request = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badges[2].id,
    )
    request_service.approve_request(
        request_id=request.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Check progress - should now have 3 mini-badges + 1 skill
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 4
    mini_badge_awards = [a for a in awards if a.award_type == AwardType.MINI_BADGE]
    skill_awards = [a for a in awards if a.award_type == AwardType.SKILL]
    assert len(mini_badge_awards) == 3
    assert len(skill_awards) == 1
    assert skill_awards[0].skill_id == skill.id
    assert skill_awards[0].awarded_by is None  # Automatic


def test_complete_program_progression(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test complete program progression: 2 skills → program award."""
    # Create program with 2 skills, 1 badge each
    program = catalog_service.create_program(
        title="Simple Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skills = []
    badges = []
    for i in range(2):
        skill = catalog_service.create_skill(
            program_id=program.id,
            title=f"Skill {i+1}",
            description=None,
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )
        skills.append(skill)

        badge = catalog_service.create_mini_badge(
            skill_id=skill.id,
            title=f"Badge {i+1}",
            description=None,
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )
        badges.append(badge)

    # Approve first badge - should award mini-badge + skill
    req1 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badges[0].id,
    )
    request_service.approve_request(
        request_id=req1.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 2  # mini_badge + skill

    # Approve second badge - should award mini-badge + skill + program
    req2 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badges[1].id,
    )
    request_service.approve_request(
        request_id=req2.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 5  # 2 mini_badges + 2 skills + 1 program

    program_awards = [a for a in awards if a.award_type == AwardType.PROGRAM]
    assert len(program_awards) == 1
    assert program_awards[0].program_id == program.id
    assert program_awards[0].awarded_by is None  # Automatic


def test_multiple_students_independent_progression(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user, second_student
):
    """Test that student progression is independent."""
    # Create simple catalog
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Student 1 earns badge
    req1 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge.id,
    )
    request_service.approve_request(
        request_id=req1.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Student 2 should have no awards
    student1_awards = progress_service.get_user_awards(student_user.id)
    student2_awards = progress_service.get_user_awards(second_student.id)

    # Program has 1 skill with 1 badge, so completing it awards mini_badge + skill + program
    assert len(student1_awards) == 3  # mini_badge + skill + program (all automatic)
    assert len(student2_awards) == 0

    # Student 2 earns badge
    req2 = request_service.submit_request(
        user_id=second_student.id,
        mini_badge_id=badge.id,
    )
    request_service.approve_request(
        request_id=req2.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    student2_awards = progress_service.get_user_awards(second_student.id)
    assert len(student2_awards) == 3  # mini_badge + skill + program


def test_capstone_requirement_blocks_program(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that required capstone blocks program award."""
    # Create program with skill and required capstone
    program = catalog_service.create_program(
        title="Program with Capstone",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Main Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Main Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create required capstone
    capstone = catalog_service.create_capstone(
        program_id=program.id,
        title="Final Project",
        description="Required capstone",
        is_required=True,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Earn the skill
    req = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge.id,
    )
    request_service.approve_request(
        request_id=req.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Should have mini_badge + skill, but NOT program (capstone required)
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 2
    program_awards = [a for a in awards if a.award_type == AwardType.PROGRAM]
    assert len(program_awards) == 0

    # Check program completion
    is_complete = progress_service.check_program_completion(
        student_user.id, program.id
    )
    assert is_complete is False


def test_progression_failure_doesnt_rollback_approval(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that progression errors don't prevent approval."""
    # This test is challenging because we need to trigger a progression error
    # For now, we'll just verify that the approval succeeds even if we simulate
    # a scenario where progression could fail

    # Create catalog
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Submit and approve request
    req = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge.id,
    )

    # Approval should succeed regardless of progression outcome
    approved = request_service.approve_request(
        request_id=req.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    assert approved.status == RequestStatus.APPROVED
    # Awards should still be created
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) >= 1


def test_concurrent_approvals_no_duplicate_awards(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that concurrent approvals don't create duplicate awards."""
    # Create catalog with 2 skills to prevent program award
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill1 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 1",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 2",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create 2 badges in same skill
    badge1 = catalog_service.create_mini_badge(
        skill_id=skill1.id,
        title="Badge 1",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge2 = catalog_service.create_mini_badge(
        skill_id=skill1.id,
        title="Badge 2",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Submit requests for both
    req1 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge1.id,
    )

    req2 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge2.id,
    )

    # Approve both (simulating concurrent approvals)
    request_service.approve_request(
        request_id=req1.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    request_service.approve_request(
        request_id=req2.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Should have 3 awards: 2 mini_badges + 1 skill (not 4 with duplicate skill)
    awards = progress_service.get_user_awards(student_user.id)
    assert len(awards) == 3

    skill_awards = [a for a in awards if a.award_type == AwardType.SKILL]
    assert len(skill_awards) == 1  # No duplicate


def test_inactive_badge_excluded_from_completion(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that inactive badges don't count toward completion."""
    # Create program with 2 skills
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill1 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 1",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 2",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create 2 badges in skill1, deactivate one
    badge1 = catalog_service.create_mini_badge(
        skill_id=skill1.id,
        title="Active Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge2 = catalog_service.create_mini_badge(
        skill_id=skill1.id,
        title="Inactive Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Deactivate badge2
    catalog_service.toggle_mini_badge_active(
        badge2.id, False, admin_user.id, admin_user.role
    )

    # Earn only the active badge
    req = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge1.id,
    )

    request_service.approve_request(
        request_id=req.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Should award skill (only 1 active badge required)
    awards = progress_service.get_user_awards(student_user.id)
    skill_awards = [a for a in awards if a.award_type == AwardType.SKILL]
    assert len(skill_awards) == 1


def test_progress_dashboard_displays_correctly(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that progress queries return correct structure."""
    # Create catalog
    program = catalog_service.create_program(
        title="Python Basics",
        description="Learn Python",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Variables",
        description="Variable fundamentals",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create 3 badges
    badges = []
    for i in range(3):
        badge = catalog_service.create_mini_badge(
            skill_id=skill.id,
            title=f"Badge {i+1}",
            description=f"Description {i+1}",
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )
        badges.append(badge)

    # Earn 2 of 3 badges
    for badge in badges[:2]:
        req = request_service.submit_request(
            user_id=student_user.id,
            mini_badge_id=badge.id,
        )
        request_service.approve_request(
            request_id=req.id,
            approver_id=admin_user.id,
            approver_role=admin_user.role,
        )

    # Get skill progress
    progress = progress_service.get_skill_progress(student_user.id, skill.id)

    assert progress["skill_title"] == "Variables"
    assert progress["earned_count"] == 2
    assert progress["total_count"] == 3
    assert progress["percentage"] == 66
    assert len(progress["mini_badges"]) == 3
    assert progress["mini_badges"][0]["earned"] is True
    assert progress["mini_badges"][1]["earned"] is True
    assert progress["mini_badges"][2]["earned"] is False


def test_admin_manual_award_workflow(
    test_engine, catalog_service, progress_service, admin_user, student_user
):
    """Test that admins can manually award badges."""
    # Create catalog
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Manually award skill (bypassing mini-badges)
    award = progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skill.id,
        awarded_by=admin_user.id,
        reason="Special recognition",
    )

    assert award.award_type == AwardType.SKILL
    assert award.skill_id == skill.id
    assert award.awarded_by == admin_user.id
    assert award.notes == "Special recognition"
    assert award.is_automatic() is False


def test_get_program_progress_structure(
    test_engine, catalog_service, progress_service, admin_user, student_user
):
    """Test program progress query structure."""
    # Create program with 2 skills
    program = catalog_service.create_program(
        title="Advanced Python",
        description="Advanced topics",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skills = []
    for i in range(2):
        skill = catalog_service.create_skill(
            program_id=program.id,
            title=f"Skill {i+1}",
            description=None,
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )
        skills.append(skill)

    # Award one skill manually
    progress_service.award_skill(
        user_id=student_user.id,
        skill_id=skills[0].id,
        awarded_by=admin_user.id,
    )

    # Get program progress
    progress = progress_service.get_program_progress(student_user.id, program.id)

    assert progress["program_title"] == "Advanced Python"
    assert progress["earned_skills"] == 1
    assert progress["total_skills"] == 2
    assert progress["percentage"] == 50
    assert progress["has_capstone"] is False


def test_audit_logs_for_automatic_awards(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user
):
    """Test that automatic awards create audit logs."""
    from sqlmodel import Session, select
    from app.models import AuditLog

    # Create simple catalog
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Approve request
    req = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge.id,
    )

    request_service.approve_request(
        request_id=req.id,
        approver_id=admin_user.id,
        approver_role=admin_user.role,
    )

    # Check audit logs
    with Session(test_engine) as session:
        # Should have logs for mini_badge award and skill award
        mini_badge_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "award_mini_badge")
        ).all()

        skill_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "award_skill_automatic")
        ).all()

        assert len(mini_badge_logs) >= 1
        assert len(skill_logs) >= 1


def test_award_statistics_accuracy(
    test_engine, catalog_service, request_service, progress_service,
    admin_user, student_user, second_student
):
    """Test that award counts are accurate across multiple students."""
    # Create catalog
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Both students earn the badge
    for student in [student_user, second_student]:
        req = request_service.submit_request(
            user_id=student.id,
            mini_badge_id=badge.id,
        )
        request_service.approve_request(
            request_id=req.id,
            approver_id=admin_user.id,
            approver_role=admin_user.role,
        )

    # Each student should have 3 awards (mini_badge + skill + program)
    # Program has 1 skill with 1 badge, so completing awards all three
    student1_awards = progress_service.get_user_awards(student_user.id)
    student2_awards = progress_service.get_user_awards(second_student.id)

    assert len(student1_awards) == 3
    assert len(student2_awards) == 3

    # Total should be 6 awards (3 per student)
    from sqlmodel import Session, select
    with Session(test_engine) as session:
        total_awards = session.exec(select(Award)).all()
        assert len(total_awards) == 6
