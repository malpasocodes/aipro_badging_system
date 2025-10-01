"""Capstone model for badge hierarchy."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Capstone(SQLModel, table=True):
    """Capstone model - optional/required program completion requirement."""

    __tablename__ = "capstones"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Parent relationship
    program_id: UUID = Field(foreign_key="programs.id", index=True)

    # Capstone details
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)

    # Requirement status
    is_required: bool = Field(default=False)  # Required for program completion?

    # Status
    is_active: bool = Field(default=True, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Capstone(id={self.id}, title='{self.title}', program_id={self.program_id}, required={self.is_required})>"
