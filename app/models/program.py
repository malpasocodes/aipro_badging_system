"""Program model for badge hierarchy."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Program(SQLModel, table=True):
    """Program model - top level of badge hierarchy."""

    __tablename__ = "programs"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Program details
    title: str = Field(max_length=200, index=True)
    description: str | None = Field(default=None)

    # Status and ordering
    is_active: bool = Field(default=True, index=True)
    position: int = Field(default=0, index=True)  # Display order

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Program(id={self.id}, title='{self.title}', active={self.is_active})>"
