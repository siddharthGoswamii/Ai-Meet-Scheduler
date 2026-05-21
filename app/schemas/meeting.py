"""
Meeting Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum


class MeetingStatus(str, Enum):
    """Meeting status enumeration"""
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ResponseStatus(str, Enum):
    """Attendee response status enumeration"""
    NONE = "none"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


# Attendee Schemas
class AttendeeCreate(BaseModel):
    """Schema for creating an attendee"""
    email: EmailStr
    display_name: Optional[str] = None
    is_required: bool = True


class AttendeeResponse(BaseModel):
    """Schema for attendee response"""
    attendee_id: str
    email: str
    display_name: Optional[str]
    response_status: ResponseStatus
    is_organizer: bool
    is_required: bool
    
    class Config:
        from_attributes = True


# Meeting Create Schema
class MeetingCreate(BaseModel):
    """Schema for creating a meeting"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    attendees: List[AttendeeCreate] = Field(..., min_length=1, max_length=250)
    location: Optional[str] = None
    is_online: bool = True
    send_invitations: bool = True
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    @field_validator('start_time')
    @classmethod
    def start_in_future(cls, v: datetime) -> datetime:
        """Validate that start_time is in the future"""
        # Make both datetimes timezone-aware for comparison
        now = datetime.now(timezone.utc)
        # If v is naive, make it UTC aware
        if v.tzinfo is None:
            v_aware = v.replace(tzinfo=timezone.utc)
        else:
            v_aware = v
        
        if v_aware <= now:
            raise ValueError('start_time must be in the future')
        return v
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: List[AttendeeCreate]) -> List[AttendeeCreate]:
        """Validate attendees list"""
        if len(v) < 1:
            raise ValueError('At least one attendee is required')
        if len(v) > 250:
            raise ValueError('Maximum 250 attendees allowed')
        
        # Check for duplicate emails
        emails = [attendee.email for attendee in v]
        if len(emails) != len(set(emails)):
            raise ValueError('Duplicate attendee emails are not allowed')
        
        return v


# Meeting Update Schema
class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeCreate]] = None
    send_updates: bool = True
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that end_time is after start_time if both provided"""
        if v and 'start_time' in info.data and info.data['start_time']:
            if v <= info.data['start_time']:
                raise ValueError('end_time must be after start_time')
        return v


# Meeting Cancel Schema
class MeetingCancel(BaseModel):
    """Schema for cancelling a meeting"""
    cancellation_message: Optional[str] = Field(None, max_length=500)
    send_cancellation: bool = True


# Organizer Schema
class OrganizerResponse(BaseModel):
    """Schema for meeting organizer"""
    user_id: str
    email: str
    display_name: str
    
    class Config:
        from_attributes = True


# Meeting Response Schema
class MeetingResponse(BaseModel):
    """Schema for meeting response"""
    meeting_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    timezone: str
    location: Optional[str]
    is_online: bool
    meeting_url: Optional[str]
    status: MeetingStatus
    organizer: OrganizerResponse
    attendees: List[AttendeeResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Meeting List Item Schema
class MeetingListItem(BaseModel):
    """Schema for meeting list item (simplified)"""
    meeting_id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: MeetingStatus
    attendee_count: int
    is_organizer: bool
    
    class Config:
        from_attributes = True


# Pagination Schema
class PaginationInfo(BaseModel):
    """Schema for pagination information"""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Meeting List Response Schema
class MeetingListResponse(BaseModel):
    """Schema for meeting list response with pagination"""
    meetings: List[MeetingListItem]
    pagination: PaginationInfo

# Made with Bob
