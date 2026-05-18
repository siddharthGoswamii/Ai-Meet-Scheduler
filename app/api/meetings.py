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
from app.models import User, Meeting, MeetingAttendee, MeetingStatus, ResponseStatus
from app.schemas import (
    MeetingCreate,
    MeetingUpdate,
    MeetingCancel,
    MeetingResponse,
    MeetingListResponse,
    MeetingListItem,
    PaginationInfo,
    AttendeeResponse,
    OrganizerResponse
)
from app.services import auth_service
from app.services.google_calendar_service import GoogleCalendarService
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meetings", tags=["Meetings"])


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
        db_meeting = Meeting(
            organizer_id=current_user.user_id,
            teams_meeting_id=google_event.get("id"),
            title=meeting_data.title,
            description=meeting_data.description,
            start_time=meeting_data.start_time,
            end_time=meeting_data.end_time,
            timezone=meeting_data.timezone,
            location=meeting_data.location,
            is_online=meeting_data.is_online,
            meeting_url=meeting_url,
            status=MeetingStatus.SCHEDULED
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
                response_status=ResponseStatus.NONE
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
            response_status=ResponseStatus.ACCEPTED
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
        
    except Exception as e:
        logger.error(f"Error creating meeting: {str(e)}")
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
        total_count = await db.scalar(count_query)
        
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
            attendee_count = await db.scalar(attendee_count_query)
            
            meeting_items.append(
                MeetingListItem(
                    meeting_id=str(meeting.meeting_id),
                    title=meeting.title,
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    status=meeting.status,
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
        if meeting.organizer_id != current_user.user_id:
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
        if meeting.organizer_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizer can update meeting"
            )
        
        # Check if meeting is cancelled
        if meeting.status == MeetingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update cancelled meeting"
            )
        
        # Update via Google Calendar API
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
                    response_status=ResponseStatus.NONE
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
        if meeting.organizer_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizer can cancel meeting"
            )
        
        # Check if already cancelled
        if meeting.status == MeetingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting is already cancelled"
            )
        
        # Cancel via Google Calendar API
        access_token = auth_service.decrypt_token(current_user.access_token)
        refresh_token = auth_service.decrypt_token(current_user.refresh_token) if current_user.refresh_token else ""
        google_service = GoogleCalendarService(access_token, refresh_token)
        
        await google_service.cancel_meeting(
            meeting.teams_meeting_id,
            cancel_data.cancellation_message
        )
        
        # Update database
        meeting.status = MeetingStatus.CANCELLED
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
    
    return MeetingResponse(
        meeting_id=str(meeting.meeting_id),
        title=meeting.title,
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        timezone=meeting.timezone,
        location=meeting.location,
        is_online=meeting.is_online,
        meeting_url=meeting.meeting_url,
        status=meeting.status,
        organizer=OrganizerResponse(
            user_id=str(organizer.user_id),
            email=organizer.email,
            display_name=organizer.display_name
        ),
        attendees=[
            AttendeeResponse(
                attendee_id=str(a.attendee_id),
                email=a.email,
                display_name=a.display_name,
                response_status=a.response_status,
                is_organizer=a.is_organizer,
                is_required=a.is_required
            )
            for a in attendees
        ],
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    )

# Made with Bob
