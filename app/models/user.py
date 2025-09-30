"""User model for authentication and role management."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    ASSISTANT = "assistant"
    STUDENT = "student"


class User(SQLModel, table=True):
    """User model for authentication and role management."""
    
    __tablename__ = "users"
    
    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Google OAuth fields
    google_sub: str = Field(unique=True, index=True)  # Google's unique user ID
    email: str = Field(unique=True, index=True)
    
    # Role and status
    role: UserRole = Field(default=UserRole.STUDENT)
    is_active: bool = Field(default=True)
    
    # Tracking fields
    last_login_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Onboarding fields (Phase 3)
    username: Optional[str] = Field(default=None, max_length=50)
    substack_email: Optional[str] = Field(default=None)
    meetup_email: Optional[str] = Field(default=None)
    onboarding_completed_at: Optional[datetime] = Field(default=None)
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    def is_assistant(self) -> bool:
        """Check if user has assistant role."""
        return self.role == UserRole.ASSISTANT
    
    def is_student(self) -> bool:
        """Check if user has student role."""
        return self.role == UserRole.STUDENT
    
    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles

    def is_onboarded(self) -> bool:
        """Check if user has completed onboarding."""
        return (
            self.username is not None
            and self.substack_email is not None
            and self.meetup_email is not None
            and self.onboarding_completed_at is not None
        )