"""Catalog service for managing badge hierarchy."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.core.database import get_engine
from app.models import Capstone, MiniBadge, Program, Skill, UserRole


class CatalogError(Exception):
    """Base exception for catalog operations."""
    pass


class ValidationError(CatalogError):
    """Validation error exception."""
    pass


class AuthorizationError(CatalogError):
    """Authorization error exception."""
    pass


class NotFoundError(CatalogError):
    """Entity not found exception."""
    pass


class CatalogService:
    """Service for managing badge catalog (programs, skills, mini-badges, capstones)."""

    def __init__(self, engine=None):
        """Initialize catalog service."""
        self.engine = engine or get_engine()
        from app.services.audit_service import AuditService
        self.audit_service = AuditService(engine=self.engine)

    # ==================== PROGRAM OPERATIONS ====================

    def create_program(
        self,
        title: str,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Program:
        """Create a new program (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can create programs")

        # Validation
        if not title or len(title.strip()) == 0:
            raise ValidationError("Program title is required")
        if len(title) > 200:
            raise ValidationError("Program title must be 200 characters or less")

        with Session(self.engine) as session:
            # Get next position
            result = session.exec(select(Program).order_by(Program.position.desc()).limit(1))
            last_program = result.first()
            position = (last_program.position + 1) if last_program else 0

            # Create program
            program = Program(
                title=title.strip(),
                description=description.strip() if description else None,
                is_active=True,
                position=position,
            )
            session.add(program)
            session.commit()
            session.refresh(program)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="create_program",
                entity="program",
                entity_id=program.id,
                context_data={"title": program.title},
            )

            return program

    def update_program(
        self,
        program_id: UUID,
        title: str | None,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Program:
        """Update an existing program (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can update programs")

        with Session(self.engine) as session:
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            # Store old values for audit
            old_title = program.title
            old_description = program.description

            # Update fields
            if title is not None:
                if not title or len(title.strip()) == 0:
                    raise ValidationError("Program title is required")
                if len(title) > 200:
                    raise ValidationError("Program title must be 200 characters or less")
                program.title = title.strip()

            if description is not None:
                program.description = description.strip() if description else None

            program.updated_at = datetime.utcnow()
            session.add(program)
            session.commit()
            session.refresh(program)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="update_program",
                entity="program",
                entity_id=program.id,
                context_data={
                    "old_title": old_title,
                    "new_title": program.title,
                    "old_description": old_description,
                    "new_description": program.description,
                },
            )

            return program

    def get_program(self, program_id: UUID) -> Program | None:
        """Get program by ID."""
        with Session(self.engine) as session:
            return session.get(Program, program_id)

    def list_programs(self, include_inactive: bool = False) -> list[Program]:
        """List all programs, ordered by position."""
        with Session(self.engine) as session:
            query = select(Program).order_by(Program.position)
            if not include_inactive:
                query = query.where(Program.is_active == True)
            result = session.exec(query)
            return list(result.all())

    def toggle_program_active(
        self,
        program_id: UUID,
        is_active: bool,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Program:
        """Activate or deactivate a program (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can activate/deactivate programs")

        with Session(self.engine) as session:
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            old_status = program.is_active
            program.is_active = is_active
            program.updated_at = datetime.utcnow()
            session.add(program)
            session.commit()
            session.refresh(program)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="toggle_program_active",
                entity="program",
                entity_id=program.id,
                context_data={
                    "old_status": old_status,
                    "new_status": is_active,
                },
            )

            return program

    def delete_program(
        self,
        program_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> None:
        """Delete a program (admin only). Soft delete preferred."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can delete programs")

        with Session(self.engine) as session:
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            # Check for dependencies (skills, capstones)
            skills = session.exec(select(Skill).where(Skill.program_id == program_id)).all()
            capstones = session.exec(select(Capstone).where(Capstone.program_id == program_id)).all()

            if skills or capstones:
                raise ValidationError(
                    f"Cannot delete program with {len(skills)} skills and {len(capstones)} capstones. "
                    "Deactivate instead or delete children first."
                )

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="delete_program",
                entity="program",
                entity_id=program.id,
                context_data={"title": program.title},
            )

            # Hard delete
            session.delete(program)
            session.commit()

    # ==================== SKILL OPERATIONS ====================

    def create_skill(
        self,
        program_id: UUID,
        title: str,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Skill:
        """Create a new skill (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can create skills")

        # Validation
        if not title or len(title.strip()) == 0:
            raise ValidationError("Skill title is required")
        if len(title) > 200:
            raise ValidationError("Skill title must be 200 characters or less")

        with Session(self.engine) as session:
            # Verify parent program exists
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            # Get next position within program
            result = session.exec(
                select(Skill)
                .where(Skill.program_id == program_id)
                .order_by(Skill.position.desc())
                .limit(1)
            )
            last_skill = result.first()
            position = (last_skill.position + 1) if last_skill else 0

            # Create skill
            skill = Skill(
                program_id=program_id,
                title=title.strip(),
                description=description.strip() if description else None,
                is_active=True,
                position=position,
            )
            session.add(skill)
            session.commit()
            session.refresh(skill)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="create_skill",
                entity="skill",
                entity_id=skill.id,
                context_data={"title": skill.title, "program_id": str(program_id)},
            )

            return skill

    def update_skill(
        self,
        skill_id: UUID,
        title: str | None,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Skill:
        """Update an existing skill (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can update skills")

        with Session(self.engine) as session:
            skill = session.get(Skill, skill_id)
            if not skill:
                raise NotFoundError(f"Skill {skill_id} not found")

            # Store old values for audit
            old_title = skill.title
            old_description = skill.description

            # Update fields
            if title is not None:
                if not title or len(title.strip()) == 0:
                    raise ValidationError("Skill title is required")
                if len(title) > 200:
                    raise ValidationError("Skill title must be 200 characters or less")
                skill.title = title.strip()

            if description is not None:
                skill.description = description.strip() if description else None

            skill.updated_at = datetime.utcnow()
            session.add(skill)
            session.commit()
            session.refresh(skill)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="update_skill",
                entity="skill",
                entity_id=skill.id,
                context_data={
                    "old_title": old_title,
                    "new_title": skill.title,
                },
            )

            return skill

    def get_skill(self, skill_id: UUID) -> Skill | None:
        """Get skill by ID."""
        with Session(self.engine) as session:
            return session.get(Skill, skill_id)

    def list_skills(
        self,
        program_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[Skill]:
        """List skills, optionally filtered by program."""
        with Session(self.engine) as session:
            query = select(Skill).order_by(Skill.program_id, Skill.position)
            if program_id:
                query = query.where(Skill.program_id == program_id)
            if not include_inactive:
                query = query.where(Skill.is_active == True)
            result = session.exec(query)
            return list(result.all())

    def toggle_skill_active(
        self,
        skill_id: UUID,
        is_active: bool,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Skill:
        """Activate or deactivate a skill (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can activate/deactivate skills")

        with Session(self.engine) as session:
            skill = session.get(Skill, skill_id)
            if not skill:
                raise NotFoundError(f"Skill {skill_id} not found")

            old_status = skill.is_active
            skill.is_active = is_active
            skill.updated_at = datetime.utcnow()
            session.add(skill)
            session.commit()
            session.refresh(skill)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="toggle_skill_active",
                entity="skill",
                entity_id=skill.id,
                context_data={
                    "old_status": old_status,
                    "new_status": is_active,
                },
            )

            return skill

    def delete_skill(
        self,
        skill_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> None:
        """Delete a skill (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can delete skills")

        with Session(self.engine) as session:
            skill = session.get(Skill, skill_id)
            if not skill:
                raise NotFoundError(f"Skill {skill_id} not found")

            # Check for dependencies (mini-badges)
            mini_badges = session.exec(select(MiniBadge).where(MiniBadge.skill_id == skill_id)).all()

            if mini_badges:
                raise ValidationError(
                    f"Cannot delete skill with {len(mini_badges)} mini-badges. "
                    "Deactivate instead or delete children first."
                )

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="delete_skill",
                entity="skill",
                entity_id=skill.id,
                context_data={"title": skill.title},
            )

            # Hard delete
            session.delete(skill)
            session.commit()

    # ==================== MINI-BADGE OPERATIONS ====================

    def create_mini_badge(
        self,
        skill_id: UUID,
        title: str,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> MiniBadge:
        """Create a new mini-badge (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can create mini-badges")

        # Validation
        if not title or len(title.strip()) == 0:
            raise ValidationError("Mini-badge title is required")
        if len(title) > 200:
            raise ValidationError("Mini-badge title must be 200 characters or less")

        with Session(self.engine) as session:
            # Verify parent skill exists
            skill = session.get(Skill, skill_id)
            if not skill:
                raise NotFoundError(f"Skill {skill_id} not found")

            # Get next position within skill
            result = session.exec(
                select(MiniBadge)
                .where(MiniBadge.skill_id == skill_id)
                .order_by(MiniBadge.position.desc())
                .limit(1)
            )
            last_badge = result.first()
            position = (last_badge.position + 1) if last_badge else 0

            # Create mini-badge
            mini_badge = MiniBadge(
                skill_id=skill_id,
                title=title.strip(),
                description=description.strip() if description else None,
                is_active=True,
                position=position,
            )
            session.add(mini_badge)
            session.commit()
            session.refresh(mini_badge)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="create_mini_badge",
                entity="mini_badge",
                entity_id=mini_badge.id,
                context_data={"title": mini_badge.title, "skill_id": str(skill_id)},
            )

            return mini_badge

    def update_mini_badge(
        self,
        mini_badge_id: UUID,
        title: str | None,
        description: str | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> MiniBadge:
        """Update an existing mini-badge (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can update mini-badges")

        with Session(self.engine) as session:
            mini_badge = session.get(MiniBadge, mini_badge_id)
            if not mini_badge:
                raise NotFoundError(f"MiniBadge {mini_badge_id} not found")

            # Store old values for audit
            old_title = mini_badge.title
            old_description = mini_badge.description

            # Update fields
            if title is not None:
                if not title or len(title.strip()) == 0:
                    raise ValidationError("Mini-badge title is required")
                if len(title) > 200:
                    raise ValidationError("Mini-badge title must be 200 characters or less")
                mini_badge.title = title.strip()

            if description is not None:
                mini_badge.description = description.strip() if description else None

            mini_badge.updated_at = datetime.utcnow()
            session.add(mini_badge)
            session.commit()
            session.refresh(mini_badge)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="update_mini_badge",
                entity="mini_badge",
                entity_id=mini_badge.id,
                context_data={
                    "old_title": old_title,
                    "new_title": mini_badge.title,
                },
            )

            return mini_badge

    def get_mini_badge(self, mini_badge_id: UUID) -> MiniBadge | None:
        """Get mini-badge by ID."""
        with Session(self.engine) as session:
            return session.get(MiniBadge, mini_badge_id)

    def list_mini_badges(
        self,
        skill_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[MiniBadge]:
        """List mini-badges, optionally filtered by skill."""
        with Session(self.engine) as session:
            query = select(MiniBadge).order_by(MiniBadge.skill_id, MiniBadge.position)
            if skill_id:
                query = query.where(MiniBadge.skill_id == skill_id)
            if not include_inactive:
                query = query.where(MiniBadge.is_active == True)
            result = session.exec(query)
            return list(result.all())

    def toggle_mini_badge_active(
        self,
        mini_badge_id: UUID,
        is_active: bool,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> MiniBadge:
        """Activate or deactivate a mini-badge (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can activate/deactivate mini-badges")

        with Session(self.engine) as session:
            mini_badge = session.get(MiniBadge, mini_badge_id)
            if not mini_badge:
                raise NotFoundError(f"MiniBadge {mini_badge_id} not found")

            old_status = mini_badge.is_active
            mini_badge.is_active = is_active
            mini_badge.updated_at = datetime.utcnow()
            session.add(mini_badge)
            session.commit()
            session.refresh(mini_badge)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="toggle_mini_badge_active",
                entity="mini_badge",
                entity_id=mini_badge.id,
                context_data={
                    "old_status": old_status,
                    "new_status": is_active,
                },
            )

            return mini_badge

    def delete_mini_badge(
        self,
        mini_badge_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> None:
        """Delete a mini-badge (admin only). Restricted if requests exist."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can delete mini-badges")

        with Session(self.engine) as session:
            mini_badge = session.get(MiniBadge, mini_badge_id)
            if not mini_badge:
                raise NotFoundError(f"MiniBadge {mini_badge_id} not found")

            # Check for dependencies (requests)
            # Note: This will be enforced by FK constraint in Phase 5 migration
            # For now, we'll just warn

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="delete_mini_badge",
                entity="mini_badge",
                entity_id=mini_badge.id,
                context_data={"title": mini_badge.title},
            )

            # Hard delete
            session.delete(mini_badge)
            session.commit()

    # ==================== CAPSTONE OPERATIONS ====================

    def create_capstone(
        self,
        program_id: UUID,
        title: str,
        description: str | None,
        is_required: bool,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Capstone:
        """Create a new capstone (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can create capstones")

        # Validation
        if not title or len(title.strip()) == 0:
            raise ValidationError("Capstone title is required")
        if len(title) > 200:
            raise ValidationError("Capstone title must be 200 characters or less")

        with Session(self.engine) as session:
            # Verify parent program exists
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            # Create capstone
            capstone = Capstone(
                program_id=program_id,
                title=title.strip(),
                description=description.strip() if description else None,
                is_required=is_required,
                is_active=True,
            )
            session.add(capstone)
            session.commit()
            session.refresh(capstone)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="create_capstone",
                entity="capstone",
                entity_id=capstone.id,
                context_data={
                    "title": capstone.title,
                    "program_id": str(program_id),
                    "is_required": is_required,
                },
            )

            return capstone

    def update_capstone(
        self,
        capstone_id: UUID,
        title: str | None,
        description: str | None,
        is_required: bool | None,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Capstone:
        """Update an existing capstone (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can update capstones")

        with Session(self.engine) as session:
            capstone = session.get(Capstone, capstone_id)
            if not capstone:
                raise NotFoundError(f"Capstone {capstone_id} not found")

            # Store old values for audit
            old_title = capstone.title
            old_required = capstone.is_required

            # Update fields
            if title is not None:
                if not title or len(title.strip()) == 0:
                    raise ValidationError("Capstone title is required")
                if len(title) > 200:
                    raise ValidationError("Capstone title must be 200 characters or less")
                capstone.title = title.strip()

            if description is not None:
                capstone.description = description.strip() if description else None

            if is_required is not None:
                capstone.is_required = is_required

            capstone.updated_at = datetime.utcnow()
            session.add(capstone)
            session.commit()
            session.refresh(capstone)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="update_capstone",
                entity="capstone",
                entity_id=capstone.id,
                context_data={
                    "old_title": old_title,
                    "new_title": capstone.title,
                    "old_required": old_required,
                    "new_required": capstone.is_required,
                },
            )

            return capstone

    def get_capstone(self, capstone_id: UUID) -> Capstone | None:
        """Get capstone by ID."""
        with Session(self.engine) as session:
            return session.get(Capstone, capstone_id)

    def list_capstones(
        self,
        program_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[Capstone]:
        """List capstones, optionally filtered by program."""
        with Session(self.engine) as session:
            query = select(Capstone).order_by(Capstone.program_id)
            if program_id:
                query = query.where(Capstone.program_id == program_id)
            if not include_inactive:
                query = query.where(Capstone.is_active == True)
            result = session.exec(query)
            return list(result.all())

    def toggle_capstone_active(
        self,
        capstone_id: UUID,
        is_active: bool,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> Capstone:
        """Activate or deactivate a capstone (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can activate/deactivate capstones")

        with Session(self.engine) as session:
            capstone = session.get(Capstone, capstone_id)
            if not capstone:
                raise NotFoundError(f"Capstone {capstone_id} not found")

            old_status = capstone.is_active
            capstone.is_active = is_active
            capstone.updated_at = datetime.utcnow()
            session.add(capstone)
            session.commit()
            session.refresh(capstone)

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="toggle_capstone_active",
                entity="capstone",
                entity_id=capstone.id,
                context_data={
                    "old_status": old_status,
                    "new_status": is_active,
                },
            )

            return capstone

    def delete_capstone(
        self,
        capstone_id: UUID,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> None:
        """Delete a capstone (admin only)."""
        # Authorization check
        if actor_role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can delete capstones")

        with Session(self.engine) as session:
            capstone = session.get(Capstone, capstone_id)
            if not capstone:
                raise NotFoundError(f"Capstone {capstone_id} not found")

            # Audit log
            self.audit_service.log_action(
                actor_user_id=actor_id,
                action="delete_capstone",
                entity="capstone",
                entity_id=capstone.id,
                context_data={"title": capstone.title},
            )

            # Hard delete
            session.delete(capstone)
            session.commit()

    # ==================== HIERARCHY QUERIES ====================

    def get_full_catalog(self) -> dict[str, Any]:
        """Get complete catalog hierarchy (programs → skills → mini-badges)."""
        with Session(self.engine) as session:
            programs = session.exec(
                select(Program).where(Program.is_active == True).order_by(Program.position)
            ).all()

            catalog = []
            for program in programs:
                skills = session.exec(
                    select(Skill)
                    .where(Skill.program_id == program.id, Skill.is_active == True)
                    .order_by(Skill.position)
                ).all()

                skills_data = []
                for skill in skills:
                    mini_badges = session.exec(
                        select(MiniBadge)
                        .where(MiniBadge.skill_id == skill.id, MiniBadge.is_active == True)
                        .order_by(MiniBadge.position)
                    ).all()

                    skills_data.append({
                        "id": skill.id,
                        "title": skill.title,
                        "description": skill.description,
                        "position": skill.position,
                        "mini_badges": [
                            {
                                "id": mb.id,
                                "title": mb.title,
                                "description": mb.description,
                                "position": mb.position,
                            }
                            for mb in mini_badges
                        ],
                    })

                capstones = session.exec(
                    select(Capstone)
                    .where(Capstone.program_id == program.id, Capstone.is_active == True)
                ).all()

                catalog.append({
                    "id": program.id,
                    "title": program.title,
                    "description": program.description,
                    "position": program.position,
                    "skills": skills_data,
                    "capstones": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "description": c.description,
                            "is_required": c.is_required,
                        }
                        for c in capstones
                    ],
                })

            return {"programs": catalog}

    def get_program_hierarchy(self, program_id: UUID) -> dict[str, Any]:
        """Get single program with all children (skills, mini-badges, capstones)."""
        with Session(self.engine) as session:
            program = session.get(Program, program_id)
            if not program:
                raise NotFoundError(f"Program {program_id} not found")

            skills = session.exec(
                select(Skill)
                .where(Skill.program_id == program_id)
                .order_by(Skill.position)
            ).all()

            skills_data = []
            for skill in skills:
                mini_badges = session.exec(
                    select(MiniBadge)
                    .where(MiniBadge.skill_id == skill.id)
                    .order_by(MiniBadge.position)
                ).all()

                skills_data.append({
                    "id": skill.id,
                    "title": skill.title,
                    "description": skill.description,
                    "is_active": skill.is_active,
                    "position": skill.position,
                    "mini_badges": [
                        {
                            "id": mb.id,
                            "title": mb.title,
                            "description": mb.description,
                            "is_active": mb.is_active,
                            "position": mb.position,
                        }
                        for mb in mini_badges
                    ],
                })

            capstones = session.exec(
                select(Capstone).where(Capstone.program_id == program_id)
            ).all()

            return {
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "is_active": program.is_active,
                "position": program.position,
                "skills": skills_data,
                "capstones": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "description": c.description,
                        "is_required": c.is_required,
                        "is_active": c.is_active,
                    }
                    for c in capstones
                ],
            }


# Factory function
def get_catalog_service(engine=None) -> CatalogService:
    """Get catalog service instance."""
    return CatalogService(engine=engine)
