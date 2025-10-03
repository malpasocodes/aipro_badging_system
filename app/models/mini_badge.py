"""MiniBadge model for badge hierarchy."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class MiniBadge(SQLModel, table=True):
    """MiniBadge model - belongs to a skill, smallest unit students can earn."""

    __tablename__ = "mini_badges"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Parent relationship
    skill_id: UUID = Field(foreign_key="skills.id", index=True)

    # Mini-badge details
    title: str = Field(max_length=200)
    description: str | None = Field(default=None)

    # Status and ordering
    is_active: bool = Field(default=True, index=True)
    position: int = Field(default=0)  # Order within skill

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<MiniBadge(id={self.id}, title='{self.title}', skill_id={self.skill_id}, active={self.is_active})>"
