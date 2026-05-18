"""
Schemas module initialization
"""
from .user import UserCreate, UserUpdate, UserResponse, TokenData
from .meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingCancel,
    MeetingResponse,
    MeetingListItem,
    MeetingListResponse,
    AttendeeCreate,
    AttendeeResponse,
    OrganizerResponse,
    PaginationInfo,
    MeetingStatus,
    ResponseStatus
)
from .ai_scheduling import (
    FindMeetingTimesRequest,
    FindMeetingTimesResponse,
    OptimalTimesRequest,
    OptimalTimesResponse,
    CalendarAvailabilityRequest,
    CalendarAvailabilityResponse,
    AutoScheduleRequest,
    AutoScheduleResponse,
    TimeSlotSuggestion,
    EnhancedTimeSlotSuggestion,
    DayOfWeek
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TokenData",
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingCancel",
    "MeetingResponse",
    "MeetingListItem",
    "MeetingListResponse",
    "AttendeeCreate",
    "AttendeeResponse",
    "OrganizerResponse",
    "PaginationInfo",
    "MeetingStatus",
    "ResponseStatus",
    "FindMeetingTimesRequest",
    "FindMeetingTimesResponse",
    "OptimalTimesRequest",
    "OptimalTimesResponse",
    "CalendarAvailabilityRequest",
    "CalendarAvailabilityResponse",
    "AutoScheduleRequest",
    "AutoScheduleResponse",
    "TimeSlotSuggestion",
    "EnhancedTimeSlotSuggestion",
    "DayOfWeek"
]

# Made with Bob
