"""
AI Scheduling Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List, Tuple
from enum import Enum


class DayOfWeek(str, Enum):
    """Day of week enumeration"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class TimeSlotSuggestion(BaseModel):
    """Schema for a suggested time slot"""
    start_time: str
    end_time: str
    duration_minutes: int
    confidence_score: float = Field(..., ge=0, le=100)
    attendee_count: int
    recommendation: str
    
    class Config:
        from_attributes = True


class AttendeeAvailability(BaseModel):
    """Schema for attendee availability information"""
    email: str
    availability: str  # "free", "busy", "tentative", "unknown"
    
    class Config:
        from_attributes = True


class EnhancedTimeSlotSuggestion(BaseModel):
    """Schema for enhanced time slot suggestion with detailed info"""
    start_time: str
    end_time: str
    confidence_score: float = Field(..., ge=0, le=100)
    attendee_availability: List[AttendeeAvailability] = []
    suggestion_reason: str
    organizer_availability: str
    duration_minutes: int
    
    class Config:
        from_attributes = True


class FindMeetingTimesRequest(BaseModel):
    """Schema for finding meeting times request"""
    attendees: List[EmailStr] = Field(..., min_length=1, max_length=250)
    duration_minutes: int = Field(..., ge=15, le=480)  # 15 min to 8 hours
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: str = "UTC"
    min_attendee_percentage: float = Field(100.0, ge=0, le=100)
    max_suggestions: int = Field(10, ge=1, le=20)
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: List[EmailStr]) -> List[EmailStr]:
        """Validate attendees list"""
        if len(v) < 1:
            raise ValueError('At least one attendee is required')
        if len(v) > 250:
            raise ValueError('Maximum 250 attendees allowed')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate attendee emails are not allowed')
        
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate date range"""
        if v and 'start_date' in info.data and info.data['start_date']:
            if v <= info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class FindMeetingTimesResponse(BaseModel):
    """Schema for finding meeting times response"""
    suggestions: List[EnhancedTimeSlotSuggestion]
    total_suggestions: int
    search_window: dict
    
    class Config:
        from_attributes = True


class OptimalTimesRequest(BaseModel):
    """Schema for AI-powered optimal times request"""
    attendees: List[EmailStr] = Field(..., min_length=1, max_length=250)
    duration_minutes: int = Field(..., ge=15, le=480)
    preferred_days: Optional[List[DayOfWeek]] = None
    preferred_start_hour: Optional[int] = Field(None, ge=0, le=23)
    preferred_end_hour: Optional[int] = Field(None, ge=0, le=23)
    timezone: str = "UTC"
    days_ahead: int = Field(14, ge=1, le=90)
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: List[EmailStr]) -> List[EmailStr]:
        """Validate attendees list"""
        if len(v) < 1:
            raise ValueError('At least one attendee is required')
        if len(v) > 250:
            raise ValueError('Maximum 250 attendees allowed')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate attendee emails are not allowed')
        
        return v
    
    @field_validator('preferred_end_hour')
    @classmethod
    def validate_hour_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate hour range"""
        if v is not None and 'preferred_start_hour' in info.data:
            start_hour = info.data['preferred_start_hour']
            if start_hour is not None and v <= start_hour:
                raise ValueError('preferred_end_hour must be after preferred_start_hour')
        return v


class OptimalTimesResponse(BaseModel):
    """Schema for AI-powered optimal times response"""
    suggestions: List[TimeSlotSuggestion]
    total_suggestions: int
    search_parameters: dict
    ai_analysis: dict
    
    class Config:
        from_attributes = True


class CalendarAvailabilityRequest(BaseModel):
    """Schema for calendar availability request"""
    attendee_emails: List[EmailStr] = Field(..., min_length=1, max_length=250)
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    
    @field_validator('attendee_emails')
    @classmethod
    def validate_attendees(cls, v: List[EmailStr]) -> List[EmailStr]:
        """Validate attendees list"""
        if len(v) < 1:
            raise ValueError('At least one attendee is required')
        if len(v) > 250:
            raise ValueError('Maximum 250 attendees allowed')
        return v
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Validate time range"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class BusyTimeSlot(BaseModel):
    """Schema for a busy time slot"""
    start: str
    end: str
    subject: str
    
    class Config:
        from_attributes = True


class AttendeeCalendar(BaseModel):
    """Schema for attendee calendar information"""
    email: str
    busy_slots: List[BusyTimeSlot]
    total_busy_minutes: int
    availability_percentage: float
    
    class Config:
        from_attributes = True


class CalendarAvailabilityResponse(BaseModel):
    """Schema for calendar availability response"""
    attendees: List[AttendeeCalendar]
    time_window: dict
    overall_availability: float
    
    class Config:
        from_attributes = True


class AutoScheduleRequest(BaseModel):
    """Schema for automatic meeting scheduling request"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    attendees: List[EmailStr] = Field(..., min_length=1, max_length=250)
    duration_minutes: int = Field(..., ge=15, le=480)
    preferred_days: Optional[List[DayOfWeek]] = None
    preferred_start_hour: Optional[int] = Field(None, ge=0, le=23)
    preferred_end_hour: Optional[int] = Field(None, ge=0, le=23)
    timezone: str = "UTC"
    days_ahead: int = Field(14, ge=1, le=90)
    location: Optional[str] = None
    is_online: bool = True
    auto_select_best_time: bool = True  # If True, automatically picks best time
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: List[EmailStr]) -> List[EmailStr]:
        """Validate attendees list"""
        if len(v) < 1:
            raise ValueError('At least one attendee is required')
        if len(v) > 250:
            raise ValueError('Maximum 250 attendees allowed')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate attendee emails are not allowed')
        
        return v
    
    @field_validator('preferred_end_hour')
    @classmethod
    def validate_hour_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate hour range"""
        if v is not None and 'preferred_start_hour' in info.data:
            start_hour = info.data['preferred_start_hour']
            if start_hour is not None and v <= start_hour:
                raise ValueError('preferred_end_hour must be after preferred_start_hour')
        return v


class AutoScheduleResponse(BaseModel):
    """Schema for automatic meeting scheduling response"""
    meeting_id: Optional[str] = None
    selected_time: Optional[TimeSlotSuggestion] = None
    alternative_times: List[TimeSlotSuggestion] = []
    status: str  # "scheduled", "suggestions_only", "failed"
    message: str
    
    class Config:
        from_attributes = True


# Made with Bob