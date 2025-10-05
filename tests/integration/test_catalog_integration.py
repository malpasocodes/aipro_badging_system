"""Integration tests for catalog workflows."""

from uuid import uuid4

import pytest

from app.models import User, UserRole
from app.services import get_catalog_service, get_request_service


@pytest.fixture
def admin_user(test_engine):
    """Create admin user for testing."""
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
    """Create student user for testing."""
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


def test_create_complete_program_hierarchy(test_engine, admin_user):
    """Test creating a complete program with skills and mini-badges."""
    catalog_service = get_catalog_service(engine=test_engine)

    # Create program
    program = catalog_service.create_program(
        title="Test Program",
        description="Test description",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    assert program.id is not None
    assert program.title == "Test Program"

    # Create skill under program
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description="Skill description",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    assert skill.id is not None
    assert skill.program_id == program.id

    # Create mini-badges under skill
    badge1 = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Badge 1",
        description="First badge",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    badge2 = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Badge 2",
        description="Second badge",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    assert badge1.skill_id == skill.id
    assert badge2.skill_id == skill.id
    assert badge1.position == 0
    assert badge2.position == 1

    # Verify hierarchy query
    hierarchy = catalog_service.get_program_hierarchy(program.id)
    assert hierarchy["title"] == "Test Program"
    assert len(hierarchy["skills"]) == 1
    assert hierarchy["skills"][0]["title"] == "Test Skill"
    assert len(hierarchy["skills"][0]["mini_badges"]) == 2


def test_cascade_deactivate_program(test_engine, admin_user):
    """Test that deactivating doesn't cascade (each entity managed separately)."""
    catalog_service = get_catalog_service(engine=test_engine)

    # Create hierarchy
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

    # Deactivate program
    catalog_service.toggle_program_active(
        program.id, False, admin_user.id, admin_user.role
    )

    # Children should still be active (no cascade)
    updated_skill = catalog_service.get_skill(skill.id)
    updated_badge = catalog_service.get_mini_badge(badge.id)

    assert updated_skill.is_active is True
    assert updated_badge.is_active is True


def test_delete_program_cascades_children(test_engine, admin_user):
    """Deleting program cascades to child entities."""
    catalog_service = get_catalog_service(engine=test_engine)

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

    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    catalog_service.delete_program(program.id, admin_user.id, admin_user.role)

    assert catalog_service.get_program(program.id) is None
    assert catalog_service.get_skill(skill.id) is None
    assert catalog_service.get_mini_badge(mini_badge.id) is None


def test_request_badge_from_catalog(test_engine, admin_user, student_user):
    """Test end-to-end: create badge in catalog, student requests it."""
    catalog_service = get_catalog_service(engine=test_engine)
    request_service = get_request_service(engine=test_engine)

    # Admin creates catalog
    program = catalog_service.create_program(
        title="Python Fundamentals",
        description="Learn Python",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Variables and Types",
        description="Master variables",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="String Manipulation",
        description="Work with strings",
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Student requests badge
    request = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=mini_badge.id,
    )

    assert request.mini_badge_id == mini_badge.id
    assert request.badge_name == "String Manipulation"
    assert request.user_id == student_user.id
    assert request.is_pending()


def test_request_inactive_badge_fails(test_engine, admin_user, student_user):
    """Test that requesting inactive badge fails."""
    catalog_service = get_catalog_service(engine=test_engine)
    request_service = get_request_service(engine=test_engine)

    # Create and deactivate badge
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

    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Deactivate badge
    catalog_service.toggle_mini_badge_active(
        mini_badge.id, False, admin_user.id, admin_user.role
    )

    # Request should fail
    from app.services.request_service import ValidationError

    with pytest.raises(ValidationError, match="not currently active"):
        request_service.submit_request(
            user_id=student_user.id,
            mini_badge_id=mini_badge.id,
        )


def test_get_full_catalog_structure(test_engine, admin_user):
    """Test retrieving full catalog with hierarchy."""
    catalog_service = get_catalog_service(engine=test_engine)

    # Create multiple programs with structure
    for i in range(2):
        program = catalog_service.create_program(
            title=f"Program {i}",
            description=None,
            actor_id=admin_user.id,
            actor_role=admin_user.role,
        )

        for j in range(2):
            skill = catalog_service.create_skill(
                program_id=program.id,
                title=f"Skill {i}.{j}",
                description=None,
                actor_id=admin_user.id,
                actor_role=admin_user.role,
            )

            for k in range(3):
                catalog_service.create_mini_badge(
                    skill_id=skill.id,
                    title=f"Badge {i}.{j}.{k}",
                    description=None,
                    actor_id=admin_user.id,
                    actor_role=admin_user.role,
                )

    # Get full catalog
    catalog = catalog_service.get_full_catalog()

    assert len(catalog["programs"]) == 2
    assert all(len(p["skills"]) == 2 for p in catalog["programs"])
    assert all(
        len(s["mini_badges"]) == 3
        for p in catalog["programs"]
        for s in p["skills"]
    )


def test_capstone_required_flag(test_engine, admin_user):
    """Test capstone required/optional flag."""
    catalog_service = get_catalog_service(engine=test_engine)

    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create required capstone
    required_capstone = catalog_service.create_capstone(
        program_id=program.id,
        title="Final Project",
        description="Required capstone",
        is_required=True,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Create optional capstone
    optional_capstone = catalog_service.create_capstone(
        program_id=program.id,
        title="Extra Credit",
        description="Optional capstone",
        is_required=False,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    assert required_capstone.is_required is True
    assert optional_capstone.is_required is False

    # Update required flag
    updated = catalog_service.update_capstone(
        capstone_id=optional_capstone.id,
        title=None,
        description=None,
        is_required=True,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    assert updated.is_required is True


def test_audit_logs_created_for_catalog_operations(test_engine, admin_user):
    """Test that all catalog CRUD operations create audit logs."""
    from sqlmodel import Session, select

    from app.models import AuditLog

    catalog_service = get_catalog_service(engine=test_engine)

    # Create program
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_user.id,
        actor_role=admin_user.role,
    )

    # Check audit log created
    with Session(test_engine) as session:
        audit_logs = session.exec(
            select(AuditLog)
            .where(AuditLog.action == "create_program")
            .where(AuditLog.entity_id == program.id)
        ).all()

        assert len(audit_logs) == 1
        assert audit_logs[0].actor_user_id == admin_user.id


def test_duplicate_pending_request_by_mini_badge_id(test_engine, student_user, admin_user):
    """Test that duplicate pending requests by mini_badge_id are prevented."""
    catalog_service = get_catalog_service(engine=test_engine)
    request_service = get_request_service(engine=test_engine)

    # Create badge
    program = catalog_service.create_program(
        title="Test", description=None, actor_id=admin_user.id, actor_role=admin_user.role
    )
    skill = catalog_service.create_skill(
        program_id=program.id, title="Test", description=None,
        actor_id=admin_user.id, actor_role=admin_user.role
    )
    badge = catalog_service.create_mini_badge(
        skill_id=skill.id, title="Test", description=None,
        actor_id=admin_user.id, actor_role=admin_user.role
    )

    # First request succeeds
    request1 = request_service.submit_request(
        user_id=student_user.id,
        mini_badge_id=badge.id,
    )
    assert request1.is_pending()

    # Second request fails
    from app.services.request_service import RequestError

    with pytest.raises(RequestError, match="already have a pending request"):
        request_service.submit_request(
            user_id=student_user.id,
            mini_badge_id=badge.id,
        )


def test_list_filters_inactive_by_default(test_engine, admin_user):
    """Test that list operations filter inactive entities by default."""
    catalog_service = get_catalog_service(engine=test_engine)

    # Create active and inactive programs
    active = catalog_service.create_program(
        title="Active", description=None, actor_id=admin_user.id, actor_role=admin_user.role
    )
    inactive = catalog_service.create_program(
        title="Inactive", description=None, actor_id=admin_user.id, actor_role=admin_user.role
    )

    catalog_service.toggle_program_active(inactive.id, False, admin_user.id, admin_user.role)

    # List without include_inactive
    programs = catalog_service.list_programs(include_inactive=False)
    program_ids = [p.id for p in programs]

    assert active.id in program_ids
    assert inactive.id not in program_ids

    # List with include_inactive
    all_programs = catalog_service.list_programs(include_inactive=True)
    all_program_ids = [p.id for p in all_programs]

    assert active.id in all_program_ids
    assert inactive.id in all_program_ids
