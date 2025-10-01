"""Progress service for badge earning and automatic progression."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import Session, select, func

from app.core.database import get_engine
from app.core.logging import get_logger
from app.models.award import Award, AwardType
from app.models.capstone import Capstone
from app.models.mini_badge import MiniBadge
from app.models.program import Program
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class ProgressError(Exception):
    """Base exception for progress-related errors."""
    pass


class DuplicateAwardError(ProgressError):
    """Award already exists for user."""
    pass


class AuthorizationError(ProgressError):
    """Authorization-related errors."""
    pass


class ProgressService:
    """Service for badge earning and automatic progression logic."""

    def __init__(self, engine=None):
        self.engine = engine
        self.audit_service = get_audit_service(engine=engine)

    def award_mini_badge(
        self,
        user_id: UUID,
        mini_badge_id: UUID,
        request_id: UUID,
        awarded_by: UUID
    ) -> List[Award]:
        """
        Award a mini-badge to a student and trigger progression checks.

        Returns list of all awards granted (mini_badge, potentially skill, potentially program).

        Args:
            user_id: ID of the student earning the badge
            mini_badge_id: ID of the mini-badge being awarded
            request_id: ID of the approved request
            awarded_by: ID of the approver

        Returns:
            List of Award objects created (mini_badge, maybe skill, maybe program)

        Raises:
            DuplicateAwardError: If user already has this mini_badge award
            ProgressError: If mini_badge or related entities not found
        """
        engine = self.engine or get_engine()
        awards_granted = []

        with Session(engine) as session:
            # Get mini_badge to find parent skill
            mini_badge = session.get(MiniBadge, mini_badge_id)
            if not mini_badge:
                raise ProgressError(f"Mini-badge {mini_badge_id} not found")

            skill_id = mini_badge.skill_id

            # Create mini_badge award
            try:
                mini_badge_award = Award(
                    user_id=user_id,
                    award_type=AwardType.MINI_BADGE,
                    mini_badge_id=mini_badge_id,
                    request_id=request_id,
                    awarded_by=awarded_by,
                    awarded_at=datetime.utcnow(),
                )
                session.add(mini_badge_award)
                session.commit()
                session.refresh(mini_badge_award)
                awards_granted.append(mini_badge_award)

                logger.info(
                    "Mini-badge awarded",
                    user_id=str(user_id),
                    mini_badge_id=str(mini_badge_id),
                    award_id=str(mini_badge_award.id),
                )

                # Audit log
                self.audit_service.log_action(
                    actor_user_id=awarded_by,
                    action="award_mini_badge",
                    entity="award",
                    entity_id=mini_badge_award.id,
                    context_data={
                        "user_id": str(user_id),
                        "mini_badge_id": str(mini_badge_id),
                        "request_id": str(request_id),
                    },
                )

            except Exception as e:
                if "UNIQUE constraint failed" in str(e) or "uq_user_mini_badge" in str(e):
                    raise DuplicateAwardError(
                        f"User {user_id} already has mini_badge {mini_badge_id}"
                    )
                raise

            # Check skill completion
            if self._check_skill_completion_internal(session, user_id, skill_id):
                try:
                    skill_award = self._award_skill_internal(
                        session, user_id, skill_id, awarded_by=None  # Automatic
                    )
                    awards_granted.append(skill_award)

                    # Get skill to find parent program
                    skill = session.get(Skill, skill_id)
                    program_id = skill.program_id

                    # Check program completion
                    if self._check_program_completion_internal(session, user_id, program_id):
                        program_award = self._award_program_internal(
                            session, user_id, program_id, awarded_by=None  # Automatic
                        )
                        awards_granted.append(program_award)

                except DuplicateAwardError:
                    # Skill/program already awarded (race condition), ignore
                    logger.warning(
                        "Skill or program already awarded (race condition)",
                        user_id=str(user_id),
                        skill_id=str(skill_id),
                    )

        return awards_granted

    def award_skill(
        self,
        user_id: UUID,
        skill_id: UUID,
        awarded_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> Award:
        """
        Award a skill badge (manual or automatic).

        Args:
            user_id: ID of the student earning the skill
            skill_id: ID of the skill being awarded
            awarded_by: ID of the admin (None for automatic)
            reason: Optional reason for manual award

        Returns:
            Created Award object

        Raises:
            DuplicateAwardError: If user already has this skill award
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            award = self._award_skill_internal(session, user_id, skill_id, awarded_by, reason)
            session.commit()
            session.refresh(award)
            return award

    def award_program(
        self,
        user_id: UUID,
        program_id: UUID,
        awarded_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> Award:
        """
        Award a program badge (manual or automatic).

        Args:
            user_id: ID of the student earning the program
            program_id: ID of the program being awarded
            awarded_by: ID of the admin (None for automatic)
            reason: Optional reason for manual award

        Returns:
            Created Award object

        Raises:
            DuplicateAwardError: If user already has this program award
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            award = self._award_program_internal(session, user_id, program_id, awarded_by, reason)
            session.commit()
            session.refresh(award)
            return award

    def _award_skill_internal(
        self,
        session: Session,
        user_id: UUID,
        skill_id: UUID,
        awarded_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> Award:
        """Internal method to award skill within existing session."""
        try:
            skill_award = Award(
                user_id=user_id,
                award_type=AwardType.SKILL,
                skill_id=skill_id,
                awarded_by=awarded_by,
                awarded_at=datetime.utcnow(),
                notes=reason,
            )
            session.add(skill_award)
            session.flush()  # Flush to check unique constraint

            logger.info(
                "Skill awarded",
                user_id=str(user_id),
                skill_id=str(skill_id),
                award_id=str(skill_award.id),
                automatic=awarded_by is None,
            )

            # Audit log
            self.audit_service.log_action(
                actor_user_id=awarded_by or user_id,
                action="award_skill_automatic" if awarded_by is None else "award_skill_manual",
                entity="award",
                entity_id=skill_award.id,
                context_data={
                    "user_id": str(user_id),
                    "skill_id": str(skill_id),
                    "automatic": awarded_by is None,
                    "reason": reason,
                },
            )

            return skill_award

        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "uq_user_skill" in str(e):
                raise DuplicateAwardError(f"User {user_id} already has skill {skill_id}")
            raise

    def _award_program_internal(
        self,
        session: Session,
        user_id: UUID,
        program_id: UUID,
        awarded_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> Award:
        """Internal method to award program within existing session."""
        try:
            program_award = Award(
                user_id=user_id,
                award_type=AwardType.PROGRAM,
                program_id=program_id,
                awarded_by=awarded_by,
                awarded_at=datetime.utcnow(),
                notes=reason,
            )
            session.add(program_award)
            session.flush()  # Flush to check unique constraint

            logger.info(
                "Program awarded",
                user_id=str(user_id),
                program_id=str(program_id),
                award_id=str(program_award.id),
                automatic=awarded_by is None,
            )

            # Audit log
            self.audit_service.log_action(
                actor_user_id=awarded_by or user_id,
                action="award_program_automatic" if awarded_by is None else "award_program_manual",
                entity="award",
                entity_id=program_award.id,
                context_data={
                    "user_id": str(user_id),
                    "program_id": str(program_id),
                    "automatic": awarded_by is None,
                    "reason": reason,
                },
            )

            return program_award

        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "uq_user_program" in str(e):
                raise DuplicateAwardError(f"User {user_id} already has program {program_id}")
            raise

    def check_skill_completion(self, user_id: UUID, skill_id: UUID) -> bool:
        """
        Check if user has earned all mini-badges for a skill.

        Args:
            user_id: ID of the student
            skill_id: ID of the skill to check

        Returns:
            True if all mini-badges earned, False otherwise
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            return self._check_skill_completion_internal(session, user_id, skill_id)

    def _check_skill_completion_internal(
        self,
        session: Session,
        user_id: UUID,
        skill_id: UUID
    ) -> bool:
        """Internal method to check skill completion within existing session."""
        # Count active mini-badges in skill
        total_statement = (
            select(func.count(MiniBadge.id))
            .where(MiniBadge.skill_id == skill_id)
            .where(MiniBadge.is_active == True)
        )
        total_mini_badges = session.exec(total_statement).first()

        # Count user's mini-badge awards in this skill
        earned_statement = (
            select(func.count(Award.id))
            .join(MiniBadge, Award.mini_badge_id == MiniBadge.id)
            .where(Award.user_id == user_id)
            .where(Award.award_type == AwardType.MINI_BADGE)
            .where(MiniBadge.skill_id == skill_id)
            .where(MiniBadge.is_active == True)
        )
        earned_mini_badges = session.exec(earned_statement).first()

        return total_mini_badges > 0 and earned_mini_badges == total_mini_badges

    def check_program_completion(self, user_id: UUID, program_id: UUID) -> bool:
        """
        Check if user has earned all skills (+ capstone if required) for a program.

        Args:
            user_id: ID of the student
            program_id: ID of the program to check

        Returns:
            True if all requirements met, False otherwise
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            return self._check_program_completion_internal(session, user_id, program_id)

    def _check_program_completion_internal(
        self,
        session: Session,
        user_id: UUID,
        program_id: UUID
    ) -> bool:
        """Internal method to check program completion within existing session."""
        # Count active skills in program
        total_statement = (
            select(func.count(Skill.id))
            .where(Skill.program_id == program_id)
            .where(Skill.is_active == True)
        )
        total_skills = session.exec(total_statement).first()

        # Count user's skill awards in this program
        earned_statement = (
            select(func.count(Award.id))
            .join(Skill, Award.skill_id == Skill.id)
            .where(Award.user_id == user_id)
            .where(Award.award_type == AwardType.SKILL)
            .where(Skill.program_id == program_id)
            .where(Skill.is_active == True)
        )
        earned_skills = session.exec(earned_statement).first()

        # Check skills requirement
        if total_skills == 0 or earned_skills < total_skills:
            return False

        # Check capstone requirement
        capstone_statement = (
            select(Capstone)
            .where(Capstone.program_id == program_id)
            .where(Capstone.is_required == True)
            .where(Capstone.is_active == True)
        )
        required_capstones = session.exec(capstone_statement).all()

        if required_capstones:
            # At least one required capstone exists - user must have earned at least one
            # (Note: We don't require ALL capstones, just at least one if any are required)
            capstone_award_statement = (
                select(func.count(Award.id))
                .where(Award.user_id == user_id)
                .where(Award.award_type == AwardType.MINI_BADGE)
                .where(Award.mini_badge_id.in_([c.id for c in required_capstones]))
            )
            earned_capstones = session.exec(capstone_award_statement).first()

            if earned_capstones == 0:
                return False

        return True

    def get_user_awards(
        self,
        user_id: UUID,
        award_type: Optional[AwardType] = None
    ) -> List[Award]:
        """
        Get all awards for a user, optionally filtered by type.

        Args:
            user_id: ID of the student
            award_type: Optional filter by award type

        Returns:
            List of Award objects, ordered by awarded_at DESC
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            statement = (
                select(Award)
                .where(Award.user_id == user_id)
            )

            if award_type:
                statement = statement.where(Award.award_type == award_type)

            statement = statement.order_by(Award.awarded_at.desc())

            results = session.exec(statement).all()
            return list(results)

    def get_skill_progress(self, user_id: UUID, skill_id: UUID) -> Dict[str, Any]:
        """
        Get progress toward a skill (earned mini-badges, total, percentage).

        Args:
            user_id: ID of the student
            skill_id: ID of the skill

        Returns:
            Dictionary with progress information
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            # Get skill info
            skill = session.get(Skill, skill_id)
            if not skill:
                raise ProgressError(f"Skill {skill_id} not found")

            # Get all active mini-badges for skill
            mini_badges_statement = (
                select(MiniBadge)
                .where(MiniBadge.skill_id == skill_id)
                .where(MiniBadge.is_active == True)
                .order_by(MiniBadge.position)
            )
            all_mini_badges = session.exec(mini_badges_statement).all()

            # Get user's awards for these mini-badges
            user_awards_statement = (
                select(Award)
                .where(Award.user_id == user_id)
                .where(Award.award_type == AwardType.MINI_BADGE)
                .where(Award.mini_badge_id.in_([mb.id for mb in all_mini_badges]))
            )
            user_awards = session.exec(user_awards_statement).all()
            earned_ids = {award.mini_badge_id for award in user_awards}

            # Build mini_badges list with earned status
            mini_badges_data = [
                {
                    "id": str(mb.id),
                    "title": mb.title,
                    "description": mb.description,
                    "earned": mb.id in earned_ids,
                }
                for mb in all_mini_badges
            ]

            earned_count = len(earned_ids)
            total_count = len(all_mini_badges)
            percentage = int((earned_count / total_count * 100)) if total_count > 0 else 0

            return {
                "skill_id": str(skill_id),
                "skill_title": skill.title,
                "skill_description": skill.description,
                "earned_count": earned_count,
                "total_count": total_count,
                "percentage": percentage,
                "mini_badges": mini_badges_data,
            }

    def get_program_progress(self, user_id: UUID, program_id: UUID) -> Dict[str, Any]:
        """
        Get progress toward a program (earned skills, total, percentage).

        Args:
            user_id: ID of the student
            program_id: ID of the program

        Returns:
            Dictionary with progress information
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            # Get program info
            program = session.get(Program, program_id)
            if not program:
                raise ProgressError(f"Program {program_id} not found")

            # Get all active skills for program
            skills_statement = (
                select(Skill)
                .where(Skill.program_id == program_id)
                .where(Skill.is_active == True)
                .order_by(Skill.position)
            )
            all_skills = session.exec(skills_statement).all()

            # Get user's skill awards
            user_awards_statement = (
                select(Award)
                .where(Award.user_id == user_id)
                .where(Award.award_type == AwardType.SKILL)
                .where(Award.skill_id.in_([s.id for s in all_skills]))
            )
            user_awards = session.exec(user_awards_statement).all()
            earned_skill_ids = {award.skill_id for award in user_awards}

            # Check capstone requirement
            capstone_statement = (
                select(Capstone)
                .where(Capstone.program_id == program_id)
                .where(Capstone.is_required == True)
                .where(Capstone.is_active == True)
            )
            required_capstones = session.exec(capstone_statement).all()
            has_capstone = len(required_capstones) > 0

            capstone_earned = False
            if has_capstone:
                # Check if user has earned any required capstone
                # (Note: Capstones are actually mini_badges, not a separate award type)
                # This is a simplified check - in practice might need more complex logic
                capstone_earned = False  # Placeholder

            earned_skills = len(earned_skill_ids)
            total_skills = len(all_skills)
            percentage = int((earned_skills / total_skills * 100)) if total_skills > 0 else 0

            return {
                "program_id": str(program_id),
                "program_title": program.title,
                "program_description": program.description,
                "earned_skills": earned_skills,
                "total_skills": total_skills,
                "percentage": percentage,
                "has_capstone": has_capstone,
                "capstone_earned": capstone_earned,
            }

    def get_all_progress(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get complete progress summary for a user.

        Args:
            user_id: ID of the student

        Returns:
            Dictionary with complete progress data
        """
        engine = self.engine or get_engine()

        with Session(engine) as session:
            # Get all user awards
            all_awards = self.get_user_awards(user_id)

            # Count by type
            mini_badge_awards = [a for a in all_awards if a.award_type == AwardType.MINI_BADGE]
            skill_awards = [a for a in all_awards if a.award_type == AwardType.SKILL]
            program_awards = [a for a in all_awards if a.award_type == AwardType.PROGRAM]

            total_earned = len(all_awards)

            # TODO: Implement in_progress and available counts
            # For now, return simplified structure
            in_progress_count = 0
            available_count = 0

            return {
                "total_earned": total_earned,
                "in_progress_count": in_progress_count,
                "available_count": available_count,
                "earned_awards": [],  # Populated by UI
                "in_progress_skills": [],  # Populated by UI
                "in_progress_programs": [],  # Populated by UI
                "available_programs": [],  # Populated by UI
            }


# Service factory function
def get_progress_service(engine=None) -> ProgressService:
    """Get an instance of ProgressService."""
    return ProgressService(engine=engine)
