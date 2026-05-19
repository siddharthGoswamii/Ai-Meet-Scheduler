# backend/api/calendar.py

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/calendar", tags=["Calendar"])

def get_calendar_service(user_tokens: dict):
    credentials = Credentials(
        token         = user_tokens["access_token"],
        refresh_token = user_tokens["refresh_token"],
        client_id     = GOOGLE_CLIENT_ID,
        client_secret = GOOGLE_CLIENT_SECRET,
        token_uri     = "https://oauth2.googleapis.com/token"
    )
    return build("calendar", "v3", credentials=credentials)


# Get user's busy slots
@router.get("/calendar/busy-slots")
def get_busy_slots(
    date: str,          # "2026-05-20"
    user = Depends(get_current_user),
    db   = Depends(get_db)
):
    service = get_calendar_service(user.tokens)

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
@router.post("/calendar/create-meeting")
def create_meeting(
    title:        str,
    start_time:   str,    # "2026-05-20T10:00:00"
    end_time:     str,    # "2026-05-20T11:00:00"
    participants: list,   # ["a@gmail.com", "b@gmail.com"]
    user = Depends(get_current_user)
):
    service = get_calendar_service(user.tokens)

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