"""
Meeting Reminder database model
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.database import Base


class ReminderType(str, enum.Enum):
    """Reminder type enumeration"""
    EMAIL = "email"
    NOTIFICATION = "notification"
    BOTH = "both"


class MeetingReminder(Base):
    """Meeting reminder model for storing reminder settings"""
    
    __tablename__ = "meeting_reminders"
    
    reminder_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.meeting_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Reminder settings
    reminder_time = Column(DateTime, nullable=False, index=True)
    reminder_type = Column(
        SQLEnum(ReminderType, name="reminder_type"),
        default=ReminderType.NOTIFICATION,
        nullable=False
    )
    
    # Status
    is_sent = Column(Boolean, default=False, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
    
    def __repr__(self):
        return f"<MeetingReminder(reminder_time='{self.reminder_time}', is_sent={self.is_sent})>"

# Made with Bob
