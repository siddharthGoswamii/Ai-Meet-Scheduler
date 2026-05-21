"""
User database model
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid
from typing import Optional

from app.db.database import Base


class User(Base):
    """User model for storing user information and authentication tokens"""
    
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    teams_user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Encrypted tokens - using Mapped for proper type checking
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # User preferences
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    organized_meetings = relationship(
        "Meeting",
        back_populates="organizer",
        foreign_keys="Meeting.organizer_id",
        cascade="all, delete-orphan"
    )
    
    attendee_records = relationship(
        "MeetingAttendee",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    reminders = relationship(
        "MeetingReminder",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}', display_name='{self.display_name}')>"

# Made with Bob
