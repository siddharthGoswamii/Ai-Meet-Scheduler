# backend/api/calendar.py

from googleapiclient.discovery import build  # type: ignore
from google.oauth2.credentials import Credentials
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
import logging

from app.core.config import settings
from app.db.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.google_calendar_service import GoogleCalendarService
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])

def get_calendar_service(user: User):
    """
    Create Google Calendar service for a user
    
    Args:
        user: User object with encrypted tokens
    
    Returns:
        Google Calendar service instance
    """
    from app.services.auth_service import auth_service
    
    # Decrypt tokens - type: ignore needed for SQLAlchemy Column types
    access_token = auth_service.decrypt_token(user.access_token)  # type: ignore
    refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token is not None else None  # type: ignore
    
    credentials = Credentials(
        token         = access_token,
        refresh_token = refresh_token,
        client_id     = settings.GOOGLE_CLIENT_ID,
        client_secret = settings.GOOGLE_CLIENT_SECRET,
        token_uri     = "https://oauth2.googleapis.com/token"
    )
    return build("calendar", "v3", credentials=credentials)


# Get user's busy slots
@router.get("/busy-slots")
async def get_busy_slots(
    date: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's busy time slots for a specific date
    
    Args:
        date: Date in format "YYYY-MM-DD"
        user: Current authenticated user
        db: Database session
    
    Returns:
        Dict with date and list of busy slots
    """
    try:
        service = get_calendar_service(user)

        # Parse the date and create proper timezone-aware datetime objects
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        
        # Create start and end of day in IST
        start_of_day = ist.localize(date_obj.replace(hour=0, minute=0, second=0))
        end_of_day = ist.localize(date_obj.replace(hour=23, minute=59, second=59))
        
        # Convert to RFC3339 format
        time_min = start_of_day.isoformat()
        time_max = end_of_day.isoformat()
        
        logger.info(f"Fetching events for {date}: {time_min} to {time_max}")

        # Get events for that day
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        logger.info(f"Found {len(events)} events for {date}")

        busy_slots = []
        for event in events:
            # Get start and end times (handle both dateTime and date formats)
            start = event["start"].get("dateTime") or event["start"].get("date")
            end = event["end"].get("dateTime") or event["end"].get("date")
            
            busy_slots.append({
                "title": event.get("summary", "Busy"),
                "start": start,
                "end": end,
                "event_id": event.get("id")
            })
            logger.info(f"Event: {event.get('summary', 'Busy')} from {start} to {end}")

        return {"date": date, "busy_slots": busy_slots, "total_events": len(busy_slots)}
        
    except Exception as e:
        logger.error(f"Error fetching busy slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch busy slots: {str(e)}"
        )

@router.get("/contacts")
async def get_contacts(
    user: User = Depends(get_current_user)
):
    """
    Get user's Google contacts
    
    Args:
        user: Current authenticated user
    
    Returns:
        List of contacts with name and email
    """
    try:
        # Decrypt tokens
        access_token = auth_service.decrypt_token(user.access_token)  # type: ignore
        refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token else None  # type: ignore
        
        # Create Google Calendar service
        google_service = GoogleCalendarService(access_token, refresh_token)
        
        # Get contacts
        contacts = await google_service.get_contacts(max_results=100)
        
        return {"contacts": contacts, "total": len(contacts)}
        
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        # Return empty list instead of error to not break the UI
        return {"contacts": [], "total": 0}



# Create a meeting with Google Meet link
@router.post("/create-meeting")
async def create_meeting(
    title: str,
    start_time: str,
    end_time: str,
    participants: list[str],
    user: User = Depends(get_current_user)
):
    """
    Create a calendar event with Google Meet link
    
    Args:
        title: Meeting title
        start_time: Start time in ISO format "YYYY-MM-DDTHH:MM:SS"
        end_time: End time in ISO format "YYYY-MM-DDTHH:MM:SS"
        participants: List of participant email addresses
        user: Current authenticated user
    
    Returns:
        Dict with event_id, meet_link, and calendar_link
    """
    service = get_calendar_service(user)

    # Build event with Google Meet
    event = {
        "summary":     title,
        "start":       {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "end":         {"dateTime": end_time,   "timeZone": "Asia/Kolkata"},
        "attendees":   [{"email": p} for p in participants],

        # ← This creates Google Meet link automatically!
        "conferenceData": {
            "createRequest": {
                "requestId":     f"meet_{start_time}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }
    }

    # Insert event
    event = service.events().insert(
        calendarId           = "primary",
        body                 = event,
        conferenceDataVersion = 1,   # needed for Meet link
        sendUpdates          = "all" # sends email invites
    ).execute()

    meet_link = event.get("hangoutLink", "")

    return {
        "event_id":  event["id"],
        "meet_link": meet_link,   # ← Google Meet URL
        "calendar_link": event.get("htmlLink")
    }


# Pydantic schemas for request/response validation
class FindFreeSlotsRequest(BaseModel):
    """Request schema for finding free time slots"""
    attendee_emails: List[EmailStr] = Field(..., min_length=1, description="List of attendee email addresses")
    duration_minutes: int = Field(..., ge=15, le=480, description="Meeting duration in minutes (15 min to 8 hours)")
    start_date: datetime = Field(..., description="Start of search window")
    end_date: datetime = Field(..., description="End of search window")
    timezone: str = Field(default="UTC", description="Timezone for the meeting")
    working_hours_start: int = Field(default=9, ge=0, le=23, description="Start of working hours (0-23)")
    working_hours_end: int = Field(default=17, ge=0, le=23, description="End of working hours (0-23)")


class TimeSlot(BaseModel):
    """Schema for a time slot"""
    start_time: str
    end_time: str
    duration_minutes: int
    confidence_score: float
    attendee_count: int
    day_of_week: str
    time_of_day: str


class FindFreeSlotsResponse(BaseModel):
    """Response schema for finding free time slots"""
    free_slots: List[TimeSlot]
    total_slots: int
    search_window: dict
    message: str


class AutoScheduleMeetingRequest(BaseModel):
    """Request schema for auto-scheduling a meeting"""
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    description: Optional[str] = Field(None, max_length=2000, description="Meeting description")
    attendee_emails: List[EmailStr] = Field(..., min_length=1, description="List of attendee email addresses")
    duration_minutes: int = Field(..., ge=15, le=480, description="Meeting duration in minutes")
    start_date: datetime = Field(..., description="Start of search window")
    end_date: datetime = Field(..., description="End of search window")
    timezone: str = Field(default="UTC", description="Timezone for the meeting")
    working_hours_start: int = Field(default=9, ge=0, le=23, description="Start of working hours")
    working_hours_end: int = Field(default=17, ge=0, le=23, description="End of working hours")
    location: Optional[str] = Field(None, description="Physical location")
    is_online: bool = Field(default=True, description="Create Google Meet link")


class AutoScheduleMeetingResponse(BaseModel):
    """Response schema for auto-scheduled meeting"""
    meeting_id: str
    event_id: str
    meet_link: Optional[str]
    calendar_link: Optional[str]
    selected_slot: TimeSlot
    alternative_slots: List[TimeSlot]
    total_slots_found: int
    message: str


@router.post("/find-free-slots", response_model=FindFreeSlotsResponse)
async def find_free_slots(
    request: FindFreeSlotsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Find time slots when all attendees are free
    
    This endpoint analyzes the Google Calendar of all attendees and finds
    common free time slots based on their availability.
    
    Args:
        request: Find free slots request parameters
        user: Current authenticated user
        db: Database session
    
    Returns:
        List of available time slots with confidence scores
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(user.access_token)  # type: ignore
        refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token else None  # type: ignore
        
        # Initialize Google Calendar service
        calendar_service = GoogleCalendarService(access_token, refresh_token)
        
        # Find common free slots
        free_slots = await calendar_service.find_common_free_slots(
            attendee_emails=request.attendee_emails,
            start_time=request.start_date,
            end_time=request.end_date,
            duration_minutes=request.duration_minutes,
            timezone=request.timezone,
            working_hours_start=request.working_hours_start,
            working_hours_end=request.working_hours_end
        )
        
        # Convert to response format
        time_slots = [
            TimeSlot(
                start_time=slot['start_time'],
                end_time=slot['end_time'],
                duration_minutes=slot['duration_minutes'],
                confidence_score=slot['confidence_score'],
                attendee_count=slot['attendee_count'],
                day_of_week=slot['day_of_week'],
                time_of_day=slot['time_of_day']
            )
            for slot in free_slots
        ]
        
        return FindFreeSlotsResponse(
            free_slots=time_slots,
            total_slots=len(time_slots),
            search_window={
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "timezone": request.timezone,
                "attendee_count": len(request.attendee_emails)
            },
            message=f"Found {len(time_slots)} available time slots for {len(request.attendee_emails)} attendees"
        )
        
    except Exception as e:
        logger.error(f"Error finding free slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find free slots: {str(e)}"
        )


@router.post("/auto-schedule", response_model=AutoScheduleMeetingResponse)
async def auto_schedule_meeting(
    request: AutoScheduleMeetingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Automatically schedule a meeting at the best available time
    
    This is the main AI-powered scheduling endpoint that:
    1. Checks Google Calendar availability for all attendees
    2. Finds time slots when everyone is free
    3. Ranks slots by confidence score (time of day, day of week, etc.)
    4. Automatically creates the meeting at the best time
    5. Sends calendar invitations to all attendees
    
    Args:
        request: Auto-schedule meeting request parameters
        user: Current authenticated user
        db: Database session
    
    Returns:
        Created meeting details with selected time slot and alternatives
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(user.access_token)  # type: ignore
        refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token else None  # type: ignore
        
        # Initialize Google Calendar service
        calendar_service = GoogleCalendarService(access_token, refresh_token)
        
        # Auto-schedule the meeting
        meeting_data = await calendar_service.auto_schedule_meeting(
            title=request.title,
            description=request.description or "",
            attendee_emails=request.attendee_emails,
            duration_minutes=request.duration_minutes,
            start_date=request.start_date,
            end_date=request.end_date,
            timezone=request.timezone,
            working_hours_start=request.working_hours_start,
            working_hours_end=request.working_hours_end,
            location=request.location,
            is_online=request.is_online
        )
        
        # Extract scheduling info
        scheduling_info = meeting_data.get('scheduling_info', {})
        selected_slot = scheduling_info.get('selected_slot', {})
        alternative_slots = scheduling_info.get('alternative_slots', [])
        
        # Convert to response format
        selected_time_slot = TimeSlot(
            start_time=selected_slot['start_time'],
            end_time=selected_slot['end_time'],
            duration_minutes=selected_slot['duration_minutes'],
            confidence_score=selected_slot['confidence_score'],
            attendee_count=selected_slot['attendee_count'],
            day_of_week=selected_slot['day_of_week'],
            time_of_day=selected_slot['time_of_day']
        )
        
        alternative_time_slots = [
            TimeSlot(
                start_time=slot['start_time'],
                end_time=slot['end_time'],
                duration_minutes=slot['duration_minutes'],
                confidence_score=slot['confidence_score'],
                attendee_count=slot['attendee_count'],
                day_of_week=slot['day_of_week'],
                time_of_day=slot['time_of_day']
            )
            for slot in alternative_slots
        ]
        
        # Extract meeting details
        meet_link = calendar_service.extract_meet_link(meeting_data)
        
        return AutoScheduleMeetingResponse(
            meeting_id=meeting_data['id'],
            event_id=meeting_data['id'],
            meet_link=meet_link,
            calendar_link=meeting_data.get('htmlLink'),
            selected_slot=selected_time_slot,
            alternative_slots=alternative_time_slots,
            total_slots_found=scheduling_info.get('total_slots_found', 0),
            message=f"Meeting '{request.title}' successfully scheduled at {selected_slot['start_time']} with {selected_slot['confidence_score']}% confidence"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error auto-scheduling meeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-schedule meeting: {str(e)}"
        )


@router.get("/attendee-availability")
async def get_attendee_availability(
    attendee_emails: str,  # Comma-separated emails
    start_date: str,  # ISO format datetime
    end_date: str,  # ISO format datetime
    timezone: str = "UTC",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed availability information for multiple attendees
    
    This endpoint retrieves free/busy information from Google Calendar
    for all specified attendees.
    
    Args:
        attendee_emails: Comma-separated list of attendee email addresses
        start_date: Start of time window (ISO format)
        end_date: End of time window (ISO format)
        timezone: Timezone for the query
        user: Current authenticated user
        db: Database session
    
    Returns:
        Detailed availability information for each attendee
    """
    try:
        # Parse parameters
        emails = [email.strip() for email in attendee_emails.split(',')]
        start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get user's access token
        access_token = auth_service.decrypt_token(user.access_token)  # type: ignore
        refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token else None  # type: ignore
        
        # Initialize Google Calendar service
        calendar_service = GoogleCalendarService(access_token, refresh_token)
        
        # Get free/busy information
        freebusy_data = await calendar_service.get_free_busy(
            attendee_emails=emails,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        
        # Process the data
        calendars = freebusy_data.get('calendars', {})
        attendee_availability = []
        
        for email in emails:
            calendar_data = calendars.get(email, {})
            busy_periods = calendar_data.get('busy', [])
            errors = calendar_data.get('errors', [])
            
            attendee_availability.append({
                'email': email,
                'busy_periods': busy_periods,
                'has_errors': len(errors) > 0,
                'errors': errors
            })
        
        return {
            'time_window': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'timezone': timezone
            },
            'attendees': attendee_availability,
            'total_attendees': len(emails)
        }
        
    except Exception as e:
        logger.error(f"Error getting attendee availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendee availability: {str(e)}"
        )


# Made with Bob