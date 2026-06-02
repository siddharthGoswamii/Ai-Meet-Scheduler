"""
Meeting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from datetime import datetime
import logging
import uuid

from app.db.database import get_db
from app.models import User, Meeting, MeetingAttendee
from app.models.meeting import MeetingStatus as ModelMeetingStatus
from app.models.meeting_attendee import ResponseStatus as ModelResponseStatus
from app.schemas import (
    MeetingCreate,
    MeetingUpdate,
    MeetingCancel,
    MeetingResponse,
    MeetingListResponse,
    MeetingListItem,
    PaginationInfo,
    AttendeeResponse,
    OrganizerResponse,
    MeetingStatus,
    ResponseStatus
)
from app.services import auth_service
from app.services.google_calendar_service import GoogleCalendarService
from app.api.auth import get_current_user
from app.services.gmail_verifier import verify_gmail_accounts
from app.utils.email_validator import validate_email_list
from datetime import timezone, timedelta
# from datetime import datetime as dt, timezone, timedelta


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meetings", tags=["Meetings"])
@router.post("/suggest")
async def suggest_meeting_slots(
    request_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        participants   = request_data.get("participants", [])
        duration_mins  = request_data.get("duration_mins", 60)
        preferred_date = request_data.get("preferred_date", "")

        # Step 1: Validate participant email format (Gmail-only)
        if participants:
            is_valid, error_msg, invalid_emails = validate_email_list(participants)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User access token not found"
            )
        access_token  = auth_service.decrypt_token(current_user.access_token)
        refresh_token = auth_service.decrypt_token(
            current_user.refresh_token
        ) if current_user.refresh_token else ""

        google_service = GoogleCalendarService(access_token, refresh_token)

        # Step 2: Verify Gmail accounts actually exist using Google People API
        if participants:
            logger.info(f"Verifying {len(participants)} Gmail accounts exist...")
            accounts_valid, verify_error, invalid_accounts = verify_gmail_accounts(
                participants,
                access_token
            )
            if not accounts_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=verify_error
                )
            logger.info(f"All {len(participants)} Gmail accounts verified successfully")

        # Parse date - handle both DD-MM-YYYY and YYYY-MM-DD formats
        if preferred_date:
            try:
                # Try DD-MM-YYYY format first (from frontend)
                date_obj = datetime.strptime(preferred_date, "%d-%m-%Y")
                logger.info(f"Parsed date (DD-MM-YYYY): {date_obj}")
            except ValueError:
                try:
                    # Try YYYY-MM-DD format
                    date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
                    logger.info(f"Parsed date (YYYY-MM-DD): {date_obj}")
                except ValueError:
                    logger.warning(f"Could not parse date '{preferred_date}', using today")
                    date_obj = datetime.now()
        else:
            date_obj = datetime.now()
            logger.info(f"No date provided, using today: {date_obj}")

        # IST timezone
        IST = timezone(timedelta(hours=5, minutes=30))

        # Query full day in IST
        start_time = date_obj.replace(hour=0,  minute=0,  second=0,  microsecond=0, tzinfo=IST)
        end_time   = date_obj.replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=IST)

        # Fetch busy slots from Google Calendar
        try:
            # Include current user's email to check their own calendar
            all_emails = list(set(participants + [current_user.email]))
            logger.info(f"Checking calendars for: {all_emails}")
            
            freebusy_data = await google_service.get_free_busy(
                attendee_emails=all_emails,
                start_time=start_time,
                end_time=end_time,
                timezone="Asia/Kolkata"
            )
            busy_slots = []
            calendars = freebusy_data.get('calendars', {})
            
            # Check ALL calendars returned (including user's own)
            for email, calendar_data in calendars.items():
                busy_periods = calendar_data.get('busy', [])
                busy_slots.extend(busy_periods)
                logger.info(f"Calendar {email}: {len(busy_periods)} busy periods")
            
            logger.info(f"Total busy slots fetched: {len(busy_slots)}")
            if busy_slots:
                logger.info(f"Busy slots: {busy_slots}")
        except Exception as e:
            logger.warning(f"Failed to fetch calendar data: {e}")
            busy_slots = []

        # Find free slots — everything in IST
        def find_free_slots_ist(busy, date_obj, duration):
            # Work hours in IST: 9AM to 6PM
            work_start = date_obj.replace(hour=9,  minute=0, second=0, microsecond=0, tzinfo=IST)
            work_end   = date_obj.replace(hour=18, minute=0, second=0, microsecond=0, tzinfo=IST)

            current = work_start
            free    = []

            for b in sorted(busy, key=lambda x: x.get("start", "")):
                try:
                    bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00")).astimezone(IST)
                    be = datetime.fromisoformat(b["end"].replace("Z",   "+00:00")).astimezone(IST)

                    if current + timedelta(minutes=duration) <= bs:
                        free.append({
                            "start": current.strftime("%H:%M"),
                            "end":   bs.strftime("%H:%M")
                        })
                    current = max(current, be)
                except Exception as e:
                    logger.warning(f"Skipping busy slot: {e}")
                    continue

            if current + timedelta(minutes=duration) <= work_end:
                free.append({
                    "start": current.strftime("%H:%M"),
                    "end":   work_end.strftime("%H:%M")
                })

            return free

        free_slots = find_free_slots_ist(busy_slots, date_obj, duration_mins)
        logger.info(f"Free slots found: {free_slots}")

        # Only use defaults if calendar fetch returned nothing AND no busy slots
        if not free_slots and not busy_slots:
            free_slots = [
                {"start": "09:00", "end": "10:00"},
                {"start": "11:00", "end": "12:00"},
                {"start": "14:00", "end": "15:00"},
                {"start": "15:30", "end": "16:30"},
            ]

        reasons = [
            "Morning slot — fresh start to the day",
            "Mid-morning — peak productivity time",
            "Post-lunch — good energy levels",
            "Afternoon — wrap up the day"
        ]

        suggestions = []
        for i, slot in enumerate(free_slots[:3]):
            suggestions.append({
                "start":  slot["start"],
                "end":    slot["end"],
                "reason": reasons[i % len(reasons)]
            })

        return {
            "date":        preferred_date,
            "suggestions": suggestions,
            "total_found": len(free_slots)
        }

    except Exception as e:
        logger.error(f"Suggest error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
# @router.post("/suggest")
# async def suggest_meeting_slots(
#     request_data: dict,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         participants   = request_data.get("participants", [])
#         duration_mins  = request_data.get("duration_mins", 60)
#         preferred_date = request_data.get("preferred_date", "")

#         # Get user tokens
#         if not current_user.access_token:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User access token not found"
#             )
#         access_token  = auth_service.decrypt_token(current_user.access_token)
#         refresh_token = auth_service.decrypt_token(
#             current_user.refresh_token
#         ) if current_user.refresh_token else ""

#         # :white_check_mark: Use Google Calendar Service
#         google_service = GoogleCalendarService(access_token, refresh_token)

#         # Get busy slots from Google Calendar
#         try:
#             # Parse the preferred date and create time range
#             from datetime import datetime, timedelta
#             if preferred_date:
#                 try:
#                     date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
#                 except:
#                     date_obj = datetime.now()
#             else:
#                 date_obj = datetime.now()
            
#             # Set time range for the entire day
#             # start_time = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
#             # end_time = date_obj.replace(hour=23, minute=59, second=59, microsecond=0)
#             IST = timezone(timedelta(hours=5, minutes=30))
#             start_time = date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=IST)
#             end_time   = date_obj.replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=IST)
            
#             # Get free/busy data from Google Calendar
#             freebusy_data = await google_service.get_free_busy(
#                 attendee_emails=participants,
#                 start_time=start_time,
#                 end_time=end_time,
#                 timezone="UTC"
#             )
            
#             # Extract busy slots from the response
#             busy_slots = []
#             calendars = freebusy_data.get('calendars', {})
#             for email in participants:
#                 calendar_data = calendars.get(email, {})
#                 busy_periods = calendar_data.get('busy', [])
#                 busy_slots.extend(busy_periods)
#         except Exception as e:
#             logger.warning(f"Failed to fetch calendar data: {e}")
#             busy_slots = []  # if calendar fetch fails use empty

#         # Find free slots manually
#         from datetime import datetime, timedelta

#         def find_free_slots(busy, date, duration):
#             # Parse the date string to get date_obj
#             try:
#                 parsed_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
#             except:
#                 parsed_date = datetime.now()
            
#             # Set work hours in UTC (9AM IST = 3:30 UTC, 6PM IST = 12:30 UTC)
#             work_start = datetime(year=parsed_date.year, month=parsed_date.month, day=parsed_date.day,
#                           hour=9, minute=30, second=0)  # 9AM IST = 3:30 UTC
#             work_end   = datetime(year=parsed_date.year, month=parsed_date.month, day=parsed_date.day,
#                           hour=, minute=30, second=0) # 6PM IST = 12:30 UTC

#             free = []
#             current = work_start

#             for b in sorted(busy, key=lambda x: x.get("start", "")):
#                 try:
#                     # Parse busy slot start time
#                     bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
#                     bs = bs.astimezone(timezone.utc).replace(tzinfo=None)  # normalize to UTC naive

#                     # Parse busy slot end time
#                     be = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
#                     be = be.astimezone(timezone.utc).replace(tzinfo=None)
#                     if current + timedelta(minutes=duration) <= bs:
#                         free.append({
#                             "start": current.strftime("%H:%M"),
#                             "end":   bs.strftime("%H:%M")
#                         })
#                     current = max(current, be)
#                 # except:
#                 #     continue
#                 except Exception as e:
#                     logger.warning(f"Skipping busy slot due to parse error: {e}")
#                     continue

#             if current + timedelta(minutes=duration) <= work_end:
#                 free.append({
#                     "start": current.strftime("%H:%M"),
#                     "end":   work_end.strftime("%H:%M")
#                 })

#             return free

#         free_slots = find_free_slots(busy_slots, preferred_date, duration_mins)

#         # If no busy slots found → generate default slots
#         if not free_slots:
#             free_slots = [
#                 {"start": "09:00", "end": "10:00"},
#                 {"start": "11:00", "end": "12:00"},
#                 {"start": "14:00", "end": "15:00"},
#                 {"start": "15:30", "end": "16:30"},
#             ]

#         # Build suggestions
#         reasons = [
#             "Morning slot — fresh start to the day :sunrise:",
#             "Mid-morning — peak productivity time :sunny:",
#             "Post-lunch — good energy levels :muscle:",
#             "Afternoon — wrap up the day :city_sunset:"
#         ]

#         suggestions = []
#         for i, slot in enumerate(free_slots[:3]):
#             suggestions.append({
#                 "start":  slot["start"],
#                 "end":    slot["end"],
#                 "reason": reasons[i % len(reasons)]
#             })

#         return {
#             "date":        preferred_date,
#             "suggestions": suggestions,
#             "total_found": len(free_slots)
#         }

#     except Exception as e:
#         logger.error(f"Suggest error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )


def find_free_slots(busy_slots: list, date: str, duration_mins: int) -> list:
    """Find free time slots in a day"""
    from datetime import datetime, timedelta

    work_start = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
    work_end   = datetime.strptime(f"{date} 18:00", "%Y-%m-%d %H:%M")
    current    = work_start
    free_slots = []

    busy_sorted = sorted(busy_slots, key=lambda x: x.get("start", ""))

    for busy in busy_sorted:
        try:
            busy_start = datetime.fromisoformat(
                busy["start"].replace("Z", "+00:00")
            ).replace(tzinfo=None)

            if current + timedelta(minutes=duration_mins) <= busy_start:
                free_slots.append({
                    "start": current.strftime("%H:%M"),
                    "end":   busy_start.strftime("%H:%M")
                })
            busy_end = datetime.fromisoformat(
                busy["end"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            current = max(current, busy_end)
        except:
            continue

    if current + timedelta(minutes=duration_mins) <= work_end:
        free_slots.append({
            "start": current.strftime("%H:%M"),
            "end":   work_end.strftime("%H:%M")
        })

    return free_slots


def get_slot_reason(index: int, start_time: str) -> str:
    """Get AI reason for slot suggestion"""
    hour = int(start_time.split(":")[0]) if start_time else 9

    if hour < 12:
        return "Morning slot — everyone is fresh and focused :sunrise:"
    elif hour < 14:
        return "Pre-lunch slot — good energy levels :sunny:"
    elif hour < 17:
        return "Afternoon slot — post-lunch productivity :muscle:"
    else:
        return "End of day slot — wrap up the day :city_sunset:"


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Google Meet meeting
    
    Args:
        meeting_data: Meeting creation data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created meeting details
    """
    try:
        # Get user's access token
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User access token not found"
            )
        access_token = auth_service.decrypt_token(current_user.access_token)
        refresh_token = auth_service.decrypt_token(current_user.refresh_token) if current_user.refresh_token else ""
        
        # Create meeting via Google Calendar API
        google_service = GoogleCalendarService(access_token, refresh_token)
        
        # Prepare attendees for Google Calendar API
        attendees_list = [
            {
                "email": attendee.email,
                "display_name": attendee.display_name,
                "is_required": attendee.is_required
            }
            for attendee in meeting_data.attendees
        ]
        
        google_event = await google_service.create_meeting(
            title=meeting_data.title,
            description=meeting_data.description or "",
            start_time=meeting_data.start_time,
            end_time=meeting_data.end_time,
            timezone=meeting_data.timezone,
            attendees=attendees_list,
            location=meeting_data.location,
            is_online=meeting_data.is_online
        )
        
        # Extract Google Meet URL from event response
        meeting_url = google_service.extract_meet_link(google_event)
        
        # Create meeting in database
        # Convert timezone-aware datetimes to naive for PostgreSQL
        start_time_naive = meeting_data.start_time.replace(tzinfo=None) if meeting_data.start_time.tzinfo else meeting_data.start_time
        end_time_naive = meeting_data.end_time.replace(tzinfo=None) if meeting_data.end_time.tzinfo else meeting_data.end_time
        
        db_meeting = Meeting(
            organizer_id=current_user.user_id,
            teams_meeting_id=google_event.get("id"),
            title=meeting_data.title,
            description=meeting_data.description,
            start_time=start_time_naive,
            end_time=end_time_naive,
            timezone=meeting_data.timezone,
            location=meeting_data.location,
            is_online=meeting_data.is_online,
            meeting_url=meeting_url,
            status=ModelMeetingStatus.SCHEDULED.value
        )
        
        db.add(db_meeting)
        await db.flush()
        
        # Add attendees
        for attendee_data in meeting_data.attendees:
            attendee = MeetingAttendee(
                meeting_id=db_meeting.meeting_id,
                email=attendee_data.email,
                display_name=attendee_data.display_name,
                is_required=attendee_data.is_required,
                is_organizer=False,
                response_status=ModelResponseStatus.NONE
            )
            db.add(attendee)
        
        # Add organizer as attendee
        organizer_attendee = MeetingAttendee(
            meeting_id=db_meeting.meeting_id,
            user_id=current_user.user_id,
            email=current_user.email,
            display_name=current_user.display_name,
            is_required=True,
            is_organizer=True,
            response_status=ModelResponseStatus.ACCEPTED
        )
        db.add(organizer_attendee)
        
        await db.commit()
        await db.refresh(db_meeting)
        
        # Fetch complete meeting with relationships
        result = await db.execute(
            select(Meeting)
            .where(Meeting.meeting_id == db_meeting.meeting_id)
        )
        meeting = result.scalar_one()
        
        return await _build_meeting_response(meeting, db)
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.exception("Error creating meeting")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create meeting: {str(e)}"
        )


@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO 8601)"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's meetings with pagination and filters
    
    Args:
        start_date: Filter meetings starting from this date
        end_date: Filter meetings ending before this date
        status_filter: Filter by meeting status
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of meetings with pagination info
    """
    try:
        # Build query
        query = select(Meeting).where(
            Meeting.organizer_id == current_user.user_id
        )
        
        # Apply filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.where(Meeting.start_time >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.where(Meeting.end_time <= end_dt)
        
        if status_filter:
            query = query.where(Meeting.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query) or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Meeting.start_time.asc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        meetings = result.scalars().all()
        
        # Build response
        meeting_items = []
        for meeting in meetings:
            # Count attendees
            attendee_count_query = select(func.count()).where(
                MeetingAttendee.meeting_id == meeting.meeting_id
            )
            attendee_count = await db.scalar(attendee_count_query) or 0
            
            meeting_items.append(
                MeetingListItem(
                    meeting_id=str(meeting.meeting_id),
                    title=str(meeting.title),
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    status=MeetingStatus(str(meeting.status)),
                    attendee_count=attendee_count,
                    is_organizer=True
                )
            )
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return MeetingListResponse(
            meetings=meeting_items,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error listing meetings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list meetings: {str(e)}"
        )


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get meeting details by ID
    
    Args:
        meeting_id: Meeting ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Meeting details
    """
    try:
        # Parse UUID
        try:
            meeting_uuid = uuid.UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        # Get meeting
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_uuid)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if user has access (organizer or attendee)
        if str(meeting.organizer_id) != str(current_user.user_id):
            attendee_result = await db.execute(
                select(MeetingAttendee).where(
                    and_(
                        MeetingAttendee.meeting_id == meeting_uuid,
                        MeetingAttendee.email == current_user.email
                    )
                )
            )
            if not attendee_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return await _build_meeting_response(meeting, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get meeting: {str(e)}"
        )


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    update_data: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update meeting details
    
    Args:
        meeting_id: Meeting ID
        update_data: Meeting update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated meeting details
    """
    try:
        # Parse UUID
        try:
            meeting_uuid = uuid.UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        # Get meeting
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_uuid)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if user is organizer
        if str(meeting.organizer_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizer can update meeting"
            )
        
        # Check if meeting is cancelled
        if meeting.status == ModelMeetingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update cancelled meeting"
            )
        
        # Update via Google Calendar API
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User access token not found"
            )
        access_token = auth_service.decrypt_token(current_user.access_token)
        refresh_token = auth_service.decrypt_token(current_user.refresh_token) if current_user.refresh_token else ""
        google_service = GoogleCalendarService(access_token, refresh_token)
        
        updates = {}
        if update_data.title:
            updates["title"] = update_data.title
        if update_data.description is not None:
            updates["description"] = update_data.description
        if update_data.start_time:
            updates["start_time"] = update_data.start_time
        if update_data.end_time:
            updates["end_time"] = update_data.end_time
        if update_data.timezone:
            updates["timezone"] = update_data.timezone
        if update_data.location is not None:
            updates["location"] = update_data.location
        if update_data.attendees:
            updates["attendees"] = [
                {
                    "email": a.email,
                    "display_name": a.display_name,
                    "is_required": a.is_required
                }
                for a in update_data.attendees
            ]
        
        # Validate teams_meeting_id exists
        if not meeting.teams_meeting_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting does not have a Google Calendar event ID"
            )
        
        await google_service.update_meeting(meeting.teams_meeting_id, updates)
        
        # Update database
        if update_data.title:
            meeting.title = update_data.title
        if update_data.description is not None:
            meeting.description = update_data.description
        if update_data.start_time:
            meeting.start_time = update_data.start_time
        if update_data.end_time:
            meeting.end_time = update_data.end_time
        if update_data.timezone:
            meeting.timezone = update_data.timezone
        if update_data.location is not None:
            meeting.location = update_data.location
        
        meeting.updated_at = datetime.utcnow()
        
        # Update attendees if provided
        if update_data.attendees:
            # Remove existing non-organizer attendees
            await db.execute(
                select(MeetingAttendee).where(
                    and_(
                        MeetingAttendee.meeting_id == meeting_uuid,
                        MeetingAttendee.is_organizer == False
                    )
                )
            )
            
            # Add new attendees
            for attendee_data in update_data.attendees:
                attendee = MeetingAttendee(
                    meeting_id=meeting.meeting_id,
                    email=attendee_data.email,
                    display_name=attendee_data.display_name,
                    is_required=attendee_data.is_required,
                    is_organizer=False,
                    response_status=ModelResponseStatus.NONE
                )
                db.add(attendee)
        
        await db.commit()
        await db.refresh(meeting)
        
        return await _build_meeting_response(meeting, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating meeting: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update meeting: {str(e)}"
        )


@router.delete("/{meeting_id}")
async def cancel_meeting(
    meeting_id: str,
    cancel_data: MeetingCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a meeting
    
    Args:
        meeting_id: Meeting ID
        cancel_data: Cancellation data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    try:
        # Parse UUID
        try:
            meeting_uuid = uuid.UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        # Get meeting
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_uuid)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if user is organizer
        if str(meeting.organizer_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizer can cancel meeting"
            )
        
        # Check if already cancelled
        if meeting.status == ModelMeetingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting is already cancelled"
            )
        
        # Cancel via Google Calendar API
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User access token not found"
            )
        access_token = auth_service.decrypt_token(current_user.access_token)
        refresh_token = auth_service.decrypt_token(current_user.refresh_token) if current_user.refresh_token else ""
        google_service = GoogleCalendarService(access_token, refresh_token)
        
        # Validate teams_meeting_id exists
        if not meeting.teams_meeting_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting does not have a Google Calendar event ID"
            )
        
        await google_service.cancel_meeting(
            meeting.teams_meeting_id,
            cancel_data.cancellation_message
        )
        
        # Update database
        meeting.status = ModelMeetingStatus.CANCELLED
        meeting.cancelled_at = datetime.utcnow()
        meeting.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "message": "Meeting cancelled successfully",
            "meeting_id": str(meeting.meeting_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling meeting: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel meeting: {str(e)}"
        )


async def _build_meeting_response(meeting: Meeting, db: AsyncSession) -> MeetingResponse:
    """
    Build complete meeting response with all relationships
    
    Args:
        meeting: Meeting model instance
        db: Database session
    
    Returns:
        MeetingResponse schema
    """
    # Get organizer
    organizer_result = await db.execute(
        select(User).where(User.user_id == meeting.organizer_id)
    )
    organizer = organizer_result.scalar_one()
    
    # Get attendees
    attendees_result = await db.execute(
        select(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting.meeting_id)
    )
    attendees = attendees_result.scalars().all()
    
    meeting_status_raw = str(meeting.status)
    meeting_status_value = meeting_status_raw.split(".")[-1].lower()
    
    return MeetingResponse(
        meeting_id=str(meeting.meeting_id),
        title=str(meeting.title),
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        timezone=str(meeting.timezone),
        location=meeting.location,
        is_online=meeting.is_online,
        meeting_url=meeting.meeting_url,
        status=MeetingStatus(meeting_status_value),
        organizer=OrganizerResponse(
            user_id=str(organizer.user_id),
            email=str(organizer.email),
            display_name=str(organizer.display_name)
        ),
        attendees=[
            AttendeeResponse(
                attendee_id=str(a.attendee_id),
                email=str(a.email),
                display_name=a.display_name,
                response_status=ResponseStatus(
                    str(a.response_status).split(".")[-1].lower()
                ),
                is_organizer=a.is_organizer,
                is_required=a.is_required
            )
            for a in attendees
        ],
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    )

# Made with Bob
