"""Skill model for badge hierarchy."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Skill(SQLModel, table=True):
    """Skill model - belongs to a program, contains mini-badges."""

    __tablename__ = "skills"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Parent relationship
    program_id: UUID = Field(foreign_key="programs.id", index=True)

    # Skill details
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)

    # Status and ordering
    is_active: bool = Field(default=True, index=True)
    position: int = Field(default=0)  # Order within program

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Skill(id={self.id}, title='{self.title}', program_id={self.program_id}, active={self.is_active})>"
