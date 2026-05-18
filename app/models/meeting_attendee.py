"""
Meeting Attendee database model
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.database import Base


class ResponseStatus(str, enum.Enum):
    """Attendee response status enumeration"""
    NONE = "none"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class MeetingAttendee(Base):
    """Meeting attendee model for storing participant information"""
    
    __tablename__ = "meeting_attendees"
    
    attendee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.meeting_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True, index=True)
    
    # Attendee information
    email = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    
    # Response status
    response_status = Column(
        SQLEnum(ResponseStatus, name="response_status"),
        default=ResponseStatus.NONE,
        nullable=False
    )
    
    # Attendee properties
    is_organizer = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_time = Column(DateTime, nullable=True)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="attendees")
    user = relationship("User", back_populates="attendee_records")
    
    def __repr__(self):
        return f"<MeetingAttendee(email='{self.email}', response='{self.response_status}')>"

# Made with Bob
