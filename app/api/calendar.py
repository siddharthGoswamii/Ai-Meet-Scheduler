# backend/api/calendar.py

from googleapiclient.discovery import build  # type: ignore
from google.oauth2.credentials import Credentials
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.api.auth import get_current_user
from app.models.user import User

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
    service = get_calendar_service(user)

    # Get events for that day
    events_result = service.events().list(
        calendarId  = "primary",
        timeMin     = f"{date}T00:00:00Z",
        timeMax     = f"{date}T23:59:59Z",
        singleEvents = True,
        orderBy     = "startTime"
    ).execute()

    events = events_result.get("items", [])

    busy_slots = []
    for event in events:
        busy_slots.append({
            "title": event.get("summary", "Busy"),
            "start": event["start"].get("dateTime"),
            "end":   event["end"].get("dateTime")
        })

    return {"date": date, "busy_slots": busy_slots}


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