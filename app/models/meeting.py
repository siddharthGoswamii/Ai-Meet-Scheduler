"""
Meeting database model
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

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
    teams_meeting_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Meeting details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Time information
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Location
    location = Column(String(500), nullable=True)
    is_online = Column(Boolean, default=True, nullable=False)
    meeting_url = Column(Text, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(MeetingStatus, name="meeting_status"),
        default=MeetingStatus.SCHEDULED,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    
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
