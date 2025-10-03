"""Award model for earned badges."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, UniqueConstraint


class AwardType(str, Enum):
    """Type of badge award."""
    MINI_BADGE = "mini_badge"
    SKILL = "skill"
    PROGRAM = "program"


class Award(SQLModel, table=True):
    """Award model for earned badges.

    This model uses a polymorphic pattern where exactly one of the badge
    foreign keys (mini_badge_id, skill_id, program_id) must be set based
    on the award_type.

    Unique constraints ensure students can only earn each badge once.
    """

    __tablename__ = "awards"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Student who earned the award
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Type of award (determines which FK is set)
    award_type: AwardType = Field(index=True)

    # Polymorphic foreign keys (only one should be set based on award_type)
    mini_badge_id: UUID | None = Field(
        default=None,
        foreign_key="mini_badges.id",
        index=True
    )
    skill_id: UUID | None = Field(
        default=None,
        foreign_key="skills.id",
        index=True
    )
    program_id: UUID | None = Field(
        default=None,
        foreign_key="programs.id",
        index=True
    )

    # Original request that triggered this award (for mini_badges only)
    request_id: UUID | None = Field(
        default=None,
        foreign_key="requests.id"
    )

    # Award metadata
    awarded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    awarded_by: UUID | None = Field(
        default=None,
        foreign_key="users.id"
    )  # None for automatic awards
    notes: str | None = Field(default=None)  # Optional context

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Table-level constraints
    __table_args__ = (
        # Unique constraints: user can only earn each badge once
        UniqueConstraint('user_id', 'mini_badge_id', name='uq_user_mini_badge'),
        UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
        UniqueConstraint('user_id', 'program_id', name='uq_user_program'),
    )

    def get_badge_id(self) -> UUID:
        """Get the badge ID based on award type."""
        if self.award_type == AwardType.MINI_BADGE:
            return self.mini_badge_id
        elif self.award_type == AwardType.SKILL:
            return self.skill_id
        elif self.award_type == AwardType.PROGRAM:
            return self.program_id
        raise ValueError(f"Invalid award_type: {self.award_type}")

    def is_automatic(self) -> bool:
        """Check if award was granted automatically (vs. manually by admin)."""
        return self.awarded_by is None
