"""
Meeting database model
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid
import enum
from typing import Optional

from app.db.database import Base


class MeetingStatus(str, enum.Enum):
    """Meeting status enumeration"""
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Meeting(Base):
    """Meeting model for storing meeting information"""
    
    __tablename__ = "meetings"
    
    meeting_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    teams_meeting_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    
    # Meeting details - using Mapped for proper type checking
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Time information
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meeting_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(MeetingStatus, name="meeting_status"),
        default=MeetingStatus.SCHEDULED,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    organizer = relationship(
        "User",
        back_populates="organized_meetings",
        foreign_keys=[organizer_id]
    )
    
    attendees = relationship(
        "MeetingAttendee",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    
    reminders = relationship(
        "MeetingReminder",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Meeting(title='{self.title}', start_time='{self.start_time}', status='{self.status}')>"

# Made with Bob
