"""Unit tests for CatalogService."""

from uuid import uuid4

import pytest

from app.models import UserRole
from app.services.catalog_service import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
    get_catalog_service,
)


@pytest.fixture
def catalog_service(test_engine):
    """Create catalog service with test database."""
    return get_catalog_service(engine=test_engine)


@pytest.fixture
def admin_id():
    """Admin user ID for testing."""
    return uuid4()


@pytest.fixture
def student_id():
    """Student user ID for testing."""
    return uuid4()


# ==================== PROGRAM TESTS ====================

def test_create_program_success(catalog_service, admin_id):
    """Test successful program creation."""
    program = catalog_service.create_program(
        title="Test Program",
        description="Test description",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert program.id is not None
    assert program.title == "Test Program"
    assert program.description == "Test description"
    assert program.is_active is True
    assert program.position == 0


def test_create_program_strips_whitespace(catalog_service, admin_id):
    """Test program creation strips whitespace from title and description."""
    program = catalog_service.create_program(
        title="  Test Program  ",
        description="  Test description  ",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert program.title == "Test Program"
    assert program.description == "Test description"


def test_create_program_increments_position(catalog_service, admin_id):
    """Test program position increments correctly."""
    program1 = catalog_service.create_program(
        title="Program 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    program2 = catalog_service.create_program(
        title="Program 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert program1.position == 0
    assert program2.position == 1


def test_create_program_empty_title_fails(catalog_service, admin_id):
    """Test program creation fails with empty title."""
    with pytest.raises(ValidationError, match="title is required"):
        catalog_service.create_program(
            title="",
            description=None,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
        )


def test_create_program_title_too_long_fails(catalog_service, admin_id):
    """Test program creation fails with title > 200 chars."""
    with pytest.raises(ValidationError, match="200 characters or less"):
        catalog_service.create_program(
            title="x" * 201,
            description=None,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
        )


def test_create_program_non_admin_fails(catalog_service, student_id):
    """Test program creation fails for non-admin."""
    with pytest.raises(AuthorizationError, match="Only admins can create programs"):
        catalog_service.create_program(
            title="Test Program",
            description=None,
            actor_id=student_id,
            actor_role=UserRole.STUDENT,
        )


def test_update_program_success(catalog_service, admin_id):
    """Test successful program update."""
    program = catalog_service.create_program(
        title="Original Title",
        description="Original description",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    updated = catalog_service.update_program(
        program_id=program.id,
        title="Updated Title",
        description="Updated description",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert updated.title == "Updated Title"
    assert updated.description == "Updated description"
    assert updated.id == program.id


def test_update_program_not_found(catalog_service, admin_id):
    """Test program update fails for non-existent program."""
    with pytest.raises(NotFoundError):
        catalog_service.update_program(
            program_id=uuid4(),
            title="Updated Title",
            description=None,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
        )


def test_get_program_success(catalog_service, admin_id):
    """Test get program by ID."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    retrieved = catalog_service.get_program(program.id)
    assert retrieved is not None
    assert retrieved.id == program.id
    assert retrieved.title == "Test Program"


def test_get_program_not_found(catalog_service):
    """Test get program returns None for non-existent ID."""
    retrieved = catalog_service.get_program(uuid4())
    assert retrieved is None


def test_list_programs_active_only(catalog_service, admin_id):
    """Test listing programs shows only active programs by default."""
    active_program = catalog_service.create_program(
        title="Active Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    inactive_program = catalog_service.create_program(
        title="Inactive Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    catalog_service.toggle_program_active(
        inactive_program.id, False, admin_id, UserRole.ADMIN
    )

    programs = catalog_service.list_programs(include_inactive=False)
    program_ids = [p.id for p in programs]

    assert active_program.id in program_ids
    assert inactive_program.id not in program_ids


def test_list_programs_include_inactive(catalog_service, admin_id):
    """Test listing programs includes inactive when requested."""
    active_program = catalog_service.create_program(
        title="Active Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    inactive_program = catalog_service.create_program(
        title="Inactive Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    catalog_service.toggle_program_active(
        inactive_program.id, False, admin_id, UserRole.ADMIN
    )

    programs = catalog_service.list_programs(include_inactive=True)
    program_ids = [p.id for p in programs]

    assert active_program.id in program_ids
    assert inactive_program.id in program_ids


def test_toggle_program_active(catalog_service, admin_id):
    """Test toggling program active status."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    # Deactivate
    updated = catalog_service.toggle_program_active(
        program.id, False, admin_id, UserRole.ADMIN
    )
    assert updated.is_active is False

    # Reactivate
    updated = catalog_service.toggle_program_active(
        program.id, True, admin_id, UserRole.ADMIN
    )
    assert updated.is_active is True


def test_delete_program_success(catalog_service, admin_id):
    """Test successful program deletion."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    catalog_service.delete_program(program.id, admin_id, UserRole.ADMIN)

    # Verify deleted
    retrieved = catalog_service.get_program(program.id)
    assert retrieved is None


def test_delete_program_with_skills_fails(catalog_service, admin_id):
    """Test program deletion fails if skills exist."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    with pytest.raises(ValidationError, match="Cannot delete program"):
        catalog_service.delete_program(program.id, admin_id, UserRole.ADMIN)


# ==================== SKILL TESTS ====================

def test_create_skill_success(catalog_service, admin_id):
    """Test successful skill creation."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description="Test description",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert skill.id is not None
    assert skill.program_id == program.id
    assert skill.title == "Test Skill"
    assert skill.is_active is True
    assert skill.position == 0


def test_create_skill_invalid_program(catalog_service, admin_id):
    """Test skill creation fails for non-existent program."""
    with pytest.raises(NotFoundError):
        catalog_service.create_skill(
            program_id=uuid4(),
            title="Test Skill",
            description=None,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
        )


def test_create_skill_increments_position(catalog_service, admin_id):
    """Test skill position increments within program."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    skill1 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert skill1.position == 0
    assert skill2.position == 1


def test_list_skills_by_program(catalog_service, admin_id):
    """Test listing skills filtered by program."""
    program1 = catalog_service.create_program(
        title="Program 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    program2 = catalog_service.create_program(
        title="Program 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    skill1 = catalog_service.create_skill(
        program_id=program1.id,
        title="Skill 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill2 = catalog_service.create_skill(
        program_id=program2.id,
        title="Skill 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    program1_skills = catalog_service.list_skills(program_id=program1.id)
    skill_ids = [s.id for s in program1_skills]

    assert skill1.id in skill_ids
    assert skill2.id not in skill_ids


def test_delete_skill_with_mini_badges_fails(catalog_service, admin_id):
    """Test skill deletion fails if mini-badges exist."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    with pytest.raises(ValidationError, match="Cannot delete skill"):
        catalog_service.delete_skill(skill.id, admin_id, UserRole.ADMIN)


# ==================== MINI-BADGE TESTS ====================

def test_create_mini_badge_success(catalog_service, admin_id):
    """Test successful mini-badge creation."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description="Test description",
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert mini_badge.id is not None
    assert mini_badge.skill_id == skill.id
    assert mini_badge.title == "Test Badge"
    assert mini_badge.is_active is True
    assert mini_badge.position == 0


def test_create_mini_badge_invalid_skill(catalog_service, admin_id):
    """Test mini-badge creation fails for non-existent skill."""
    with pytest.raises(NotFoundError):
        catalog_service.create_mini_badge(
            skill_id=uuid4(),
            title="Test Badge",
            description=None,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
        )


def test_list_mini_badges_by_skill(catalog_service, admin_id):
    """Test listing mini-badges filtered by skill."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill1 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill2 = catalog_service.create_skill(
        program_id=program.id,
        title="Skill 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    badge1 = catalog_service.create_mini_badge(
        skill_id=skill1.id,
        title="Badge 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    badge2 = catalog_service.create_mini_badge(
        skill_id=skill2.id,
        title="Badge 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    skill1_badges = catalog_service.list_mini_badges(skill_id=skill1.id)
    badge_ids = [b.id for b in skill1_badges]

    assert badge1.id in badge_ids
    assert badge2.id not in badge_ids


# ==================== CAPSTONE TESTS ====================

def test_create_capstone_success(catalog_service, admin_id):
    """Test successful capstone creation."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    capstone = catalog_service.create_capstone(
        program_id=program.id,
        title="Test Capstone",
        description="Test description",
        is_required=True,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert capstone.id is not None
    assert capstone.program_id == program.id
    assert capstone.title == "Test Capstone"
    assert capstone.is_required is True
    assert capstone.is_active is True


def test_update_capstone_required_flag(catalog_service, admin_id):
    """Test updating capstone required flag."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    capstone = catalog_service.create_capstone(
        program_id=program.id,
        title="Test Capstone",
        description=None,
        is_required=False,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    updated = catalog_service.update_capstone(
        capstone_id=capstone.id,
        title=None,
        description=None,
        is_required=True,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    assert updated.is_required is True


def test_list_capstones_by_program(catalog_service, admin_id):
    """Test listing capstones filtered by program."""
    program1 = catalog_service.create_program(
        title="Program 1",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    program2 = catalog_service.create_program(
        title="Program 2",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    capstone1 = catalog_service.create_capstone(
        program_id=program1.id,
        title="Capstone 1",
        description=None,
        is_required=False,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    capstone2 = catalog_service.create_capstone(
        program_id=program2.id,
        title="Capstone 2",
        description=None,
        is_required=False,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    program1_capstones = catalog_service.list_capstones(program_id=program1.id)
    capstone_ids = [c.id for c in program1_capstones]

    assert capstone1.id in capstone_ids
    assert capstone2.id not in capstone_ids


# ==================== HIERARCHY TESTS ====================

def test_get_full_catalog(catalog_service, admin_id):
    """Test getting complete catalog hierarchy."""
    # Create program with skills and mini-badges
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    catalog = catalog_service.get_full_catalog()

    assert "programs" in catalog
    assert len(catalog["programs"]) > 0
    assert catalog["programs"][0]["title"] == "Test Program"
    assert len(catalog["programs"][0]["skills"]) == 1
    assert catalog["programs"][0]["skills"][0]["title"] == "Test Skill"
    assert len(catalog["programs"][0]["skills"][0]["mini_badges"]) == 1


def test_get_program_hierarchy(catalog_service, admin_id):
    """Test getting single program hierarchy."""
    program = catalog_service.create_program(
        title="Test Program",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    skill = catalog_service.create_skill(
        program_id=program.id,
        title="Test Skill",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )
    mini_badge = catalog_service.create_mini_badge(
        skill_id=skill.id,
        title="Test Badge",
        description=None,
        actor_id=admin_id,
        actor_role=UserRole.ADMIN,
    )

    hierarchy = catalog_service.get_program_hierarchy(program.id)

    assert hierarchy["title"] == "Test Program"
    assert len(hierarchy["skills"]) == 1
    assert hierarchy["skills"][0]["title"] == "Test Skill"
    assert len(hierarchy["skills"][0]["mini_badges"]) == 1
    assert hierarchy["skills"][0]["mini_badges"][0]["title"] == "Test Badge"
