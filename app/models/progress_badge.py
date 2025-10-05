"""ProgressBadge model for program-level progress recognition."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ProgressBadge(SQLModel, table=True):
    """Progress badge awarded directly under a program."""

    __tablename__ = "progress_badges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_id: UUID = Field(foreign_key="programs.id", index=True)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None)
    icon: str = Field(default="🎖️", max_length=32)
    is_active: bool = Field(default=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return (
            "<ProgressBadge(id={id}, title='{title}', program_id={program_id}, active={active})>".format(
                id=self.id,
                title=self.title,
                program_id=self.program_id,
                active=self.is_active,
            )
        )
