"""
AI-powered scheduling API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.models import User, Meeting, MeetingAttendee, MeetingStatus, ResponseStatus
from app.schemas.ai_scheduling import (
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
    AttendeeAvailability,
    AttendeeCalendar,
    BusyTimeSlot
)
from app.schemas.meeting import AttendeeCreate, MeetingCreate
from app.services import GraphAPIService, auth_service
from app.services.ai_scheduler import AISchedulerService
from app.api.auth import get_current_user
from app.api.meetings import create_meeting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-scheduling", tags=["AI Scheduling"])


@router.post("/find-meeting-times", response_model=FindMeetingTimesResponse)
async def find_meeting_times(
    request: FindMeetingTimesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Find optimal meeting times using Microsoft Graph findMeetingTimes API
    
    This endpoint uses Microsoft's AI to analyze calendar availability
    and suggest the best meeting times for all attendees.
    
    Args:
        request: Find meeting times request parameters
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of suggested meeting times with confidence scores
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(current_user.access_token)
        
        # Initialize AI scheduler
        ai_scheduler = AISchedulerService(access_token)
        
        # Set default date range if not provided
        start_date = request.start_date or datetime.utcnow()
        end_date = request.end_date or (start_date + timedelta(days=14))
        
        # Find meeting times
        suggestions = await ai_scheduler.find_meeting_times(
            attendees=request.attendees,
            duration_minutes=request.duration_minutes,
            start_date=start_date,
            end_date=end_date,
            timezone=request.timezone,
            min_attendee_percentage=request.min_attendee_percentage,
            max_suggestions=request.max_suggestions
        )
        
        # Convert to response format
        enhanced_suggestions = []
        for suggestion in suggestions:
            attendee_avail = [
                AttendeeAvailability(
                    email=avail.get("attendee", {}).get("emailAddress", {}).get("address", ""),
                    availability=avail.get("availability", "unknown")
                )
                for avail in suggestion.get("attendee_availability", [])
            ]
            
            enhanced_suggestions.append(
                EnhancedTimeSlotSuggestion(
                    start_time=suggestion["start_time"],
                    end_time=suggestion["end_time"],
                    confidence_score=suggestion["confidence_score"],
                    attendee_availability=attendee_avail,
                    suggestion_reason=suggestion["suggestion_reason"],
                    organizer_availability=suggestion["organizer_availability"],
                    duration_minutes=suggestion["duration_minutes"]
                )
            )
        
        return FindMeetingTimesResponse(
            suggestions=enhanced_suggestions,
            total_suggestions=len(enhanced_suggestions),
            search_window={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": request.timezone
            }
        )
        
    except Exception as e:
        logger.error(f"Error finding meeting times: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find meeting times: {str(e)}"
        )


@router.post("/suggest-optimal-times", response_model=OptimalTimesResponse)
async def suggest_optimal_times(
    request: OptimalTimesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI-powered suggestion of optimal meeting times based on preferences
    
    This endpoint uses advanced AI algorithms to analyze:
    - Calendar availability for all attendees
    - Preferred days and time ranges
    - Meeting patterns and best practices
    - Time zone considerations
    
    Args:
        request: Optimal times request parameters
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Ranked list of optimal meeting times with AI confidence scores
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(current_user.access_token)
        
        # Initialize AI scheduler
        ai_scheduler = AISchedulerService(access_token)
        
        # Prepare preferred hours tuple
        preferred_hours = None
        if request.preferred_start_hour is not None and request.preferred_end_hour is not None:
            preferred_hours = (request.preferred_start_hour, request.preferred_end_hour)
        
        # Convert preferred days to list of strings
        preferred_days = None
        if request.preferred_days:
            preferred_days = [day.value for day in request.preferred_days]
        
        # Get optimal time suggestions
        suggestions = await ai_scheduler.suggest_optimal_times(
            attendees=request.attendees,
            duration_minutes=request.duration_minutes,
            preferred_days=preferred_days,
            preferred_hours=preferred_hours,
            timezone=request.timezone,
            days_ahead=request.days_ahead
        )
        
        # Convert to response format
        time_suggestions = [
            TimeSlotSuggestion(
                start_time=s["start_time"],
                end_time=s["end_time"],
                duration_minutes=s["duration_minutes"],
                confidence_score=s["confidence_score"],
                attendee_count=s["attendee_count"],
                recommendation=s["recommendation"]
            )
            for s in suggestions
        ]
        
        # Calculate AI analysis summary
        avg_confidence = sum(s.confidence_score for s in time_suggestions) / len(time_suggestions) if time_suggestions else 0
        
        return OptimalTimesResponse(
            suggestions=time_suggestions,
            total_suggestions=len(time_suggestions),
            search_parameters={
                "attendee_count": len(request.attendees),
                "duration_minutes": request.duration_minutes,
                "preferred_days": preferred_days,
                "preferred_hours": preferred_hours,
                "days_ahead": request.days_ahead,
                "timezone": request.timezone
            },
            ai_analysis={
                "average_confidence": round(avg_confidence, 2),
                "best_time": time_suggestions[0].start_time if time_suggestions else None,
                "analysis_method": "AI-powered calendar analysis with preference optimization",
                "factors_considered": [
                    "Attendee availability",
                    "Preferred time ranges",
                    "Meeting best practices",
                    "Day of week preferences",
                    "Time zone optimization"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error suggesting optimal times: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest optimal times: {str(e)}"
        )


@router.post("/calendar-availability", response_model=CalendarAvailabilityResponse)
async def get_calendar_availability(
    request: CalendarAvailabilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed calendar availability for multiple attendees
    
    This endpoint retrieves and analyzes calendar data to show:
    - Busy time slots for each attendee
    - Overall availability percentage
    - Detailed schedule information
    
    Args:
        request: Calendar availability request parameters
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Detailed availability information for all attendees
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(current_user.access_token)
        
        # Initialize AI scheduler
        ai_scheduler = AISchedulerService(access_token)
        
        # Get calendar availability
        availability = await ai_scheduler.get_calendar_availability(
            attendee_emails=request.attendee_emails,
            start_time=request.start_time,
            end_time=request.end_time,
            timezone=request.timezone
        )
        
        # Calculate total time window in minutes
        total_minutes = (request.end_time - request.start_time).total_seconds() / 60
        
        # Process availability data
        attendee_calendars = []
        total_busy_minutes = 0
        
        for email, busy_slots in availability.items():
            # Calculate busy time for this attendee
            attendee_busy_minutes = 0
            busy_time_slots = []
            
            for slot in busy_slots:
                start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
                duration = (end - start).total_seconds() / 60
                attendee_busy_minutes += duration
                
                busy_time_slots.append(
                    BusyTimeSlot(
                        start=slot["start"],
                        end=slot["end"],
                        subject=slot["subject"]
                    )
                )
            
            total_busy_minutes += attendee_busy_minutes
            
            # Calculate availability percentage
            availability_pct = ((total_minutes - attendee_busy_minutes) / total_minutes * 100) if total_minutes > 0 else 0
            
            attendee_calendars.append(
                AttendeeCalendar(
                    email=email,
                    busy_slots=busy_time_slots,
                    total_busy_minutes=int(attendee_busy_minutes),
                    availability_percentage=round(availability_pct, 2)
                )
            )
        
        # Calculate overall availability
        avg_busy_minutes = total_busy_minutes / len(request.attendee_emails) if request.attendee_emails else 0
        overall_availability = ((total_minutes - avg_busy_minutes) / total_minutes * 100) if total_minutes > 0 else 0
        
        return CalendarAvailabilityResponse(
            attendees=attendee_calendars,
            time_window={
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "timezone": request.timezone,
                "total_minutes": int(total_minutes)
            },
            overall_availability=round(overall_availability, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting calendar availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar availability: {str(e)}"
        )


@router.post("/auto-schedule", response_model=AutoScheduleResponse)
async def auto_schedule_meeting(
    request: AutoScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically schedule a meeting at the best available time
    
    This is the main AI-powered scheduling endpoint that:
    1. Analyzes calendar availability for all attendees
    2. Applies AI algorithms to find optimal times
    3. Ranks suggestions by confidence score
    4. Optionally auto-creates the meeting at the best time
    
    Args:
        request: Auto-schedule request parameters
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Scheduled meeting details or list of suggested times
    """
    try:
        # Get user's access token
        access_token = auth_service.decrypt_token(current_user.access_token)
        
        # Initialize AI scheduler
        ai_scheduler = AISchedulerService(access_token)
        
        # Prepare preferred hours tuple
        preferred_hours = None
        if request.preferred_start_hour is not None and request.preferred_end_hour is not None:
            preferred_hours = (request.preferred_start_hour, request.preferred_end_hour)
        
        # Convert preferred days to list of strings
        preferred_days = None
        if request.preferred_days:
            preferred_days = [day.value for day in request.preferred_days]
        
        # Get optimal time suggestions
        suggestions = await ai_scheduler.suggest_optimal_times(
            attendees=request.attendees,
            duration_minutes=request.duration_minutes,
            preferred_days=preferred_days,
            preferred_hours=preferred_hours,
            timezone=request.timezone,
            days_ahead=request.days_ahead
        )
        
        if not suggestions:
            return AutoScheduleResponse(
                meeting_id=None,
                selected_time=None,
                alternative_times=[],
                status="failed",
                message="No available time slots found for the specified criteria"
            )
        
        # Convert to TimeSlotSuggestion format
        time_suggestions = [
            TimeSlotSuggestion(
                start_time=s["start_time"],
                end_time=s["end_time"],
                duration_minutes=s["duration_minutes"],
                confidence_score=s["confidence_score"],
                attendee_count=s["attendee_count"],
                recommendation=s["recommendation"]
            )
            for s in suggestions
        ]
        
        # If auto_select_best_time is True, create the meeting
        if request.auto_select_best_time and time_suggestions:
            best_time = time_suggestions[0]
            
            # Create meeting at the best time
            meeting_create = MeetingCreate(
                title=request.title,
                description=request.description,
                start_time=datetime.fromisoformat(best_time.start_time),
                end_time=datetime.fromisoformat(best_time.end_time),
                timezone=request.timezone,
                attendees=[
                    AttendeeCreate(email=email, is_required=True)
                    for email in request.attendees
                ],
                location=request.location,
                is_online=request.is_online,
                send_invitations=True
            )
            
            # Create the meeting
            meeting_response = await create_meeting(meeting_create, db, current_user)
            
            return AutoScheduleResponse(
                meeting_id=meeting_response.meeting_id,
                selected_time=best_time,
                alternative_times=time_suggestions[1:5],  # Include top 4 alternatives
                status="scheduled",
                message=f"Meeting successfully scheduled at {best_time.start_time} with {best_time.confidence_score}% confidence"
            )
        else:
            # Return suggestions only
            return AutoScheduleResponse(
                meeting_id=None,
                selected_time=time_suggestions[0],
                alternative_times=time_suggestions[1:10],  # Include top 9 alternatives
                status="suggestions_only",
                message=f"Found {len(time_suggestions)} available time slots. Select one to schedule the meeting."
            )
        
    except Exception as e:
        logger.error(f"Error auto-scheduling meeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-schedule meeting: {str(e)}"
        )


# Made with Bob