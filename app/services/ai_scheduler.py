"""
AI-powered meeting scheduler service
Analyzes calendar availability and suggests optimal meeting times
"""
import httpx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from app.core.config import settings

logger = logging.getLogger(__name__)


class AISchedulerService:
    """Service for AI-powered meeting scheduling"""
    
    def __init__(self, access_token: str):
        """
        Initialize AI Scheduler service with access token
        
        Args:
            access_token: User's access token for Microsoft Graph API
        """
        self.access_token = access_token
        self.base_url = settings.GRAPH_API_ENDPOINT
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def find_meeting_times(
        self,
        attendees: List[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        timezone: str = "UTC",
        min_attendee_percentage: float = 100.0,
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find optimal meeting times using Microsoft Graph findMeetingTimes API
        
        Args:
            attendees: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            start_date: Start of search window
            end_date: End of search window
            timezone: Timezone for the meeting
            min_attendee_percentage: Minimum percentage of attendees required
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of suggested meeting time slots with confidence scores
        """
        try:
            # Prepare request body for findMeetingTimes
            request_body = {
                "attendees": [
                    {
                        "type": "required",
                        "emailAddress": {
                            "address": email
                        }
                    }
                    for email in attendees
                ],
                "timeConstraint": {
                    "timeslots": [
                        {
                            "start": {
                                "dateTime": start_date.isoformat(),
                                "timeZone": timezone
                            },
                            "end": {
                                "dateTime": end_date.isoformat(),
                                "timeZone": timezone
                            }
                        }
                    ]
                },
                "meetingDuration": f"PT{duration_minutes}M",
                "returnSuggestionReasons": True,
                "minimumAttendeePercentage": min_attendee_percentage,
                "maxCandidates": max_suggestions
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/findMeetingTimes",
                    headers=self.headers,
                    json=request_body,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Process and enhance suggestions
                suggestions = []
                for suggestion in data.get("meetingTimeSuggestions", []):
                    enhanced_suggestion = self._enhance_suggestion(
                        suggestion,
                        attendees,
                        duration_minutes
                    )
                    suggestions.append(enhanced_suggestion)
                
                return suggestions
                
        except Exception as e:
            logger.error(f"Error finding meeting times: {str(e)}")
            raise
    
    async def get_calendar_availability(
        self,
        attendee_emails: List[str],
        start_time: datetime,
        end_time: datetime,
        timezone: str = "UTC"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get calendar availability for multiple attendees
        
        Args:
            attendee_emails: List of attendee email addresses
            start_time: Start of time window
            end_time: End of time window
            timezone: Timezone for the query
        
        Returns:
            Dictionary mapping email to list of busy time slots
        """
        try:
            request_body = {
                "schedules": attendee_emails,
                "startTime": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone
                },
                "endTime": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone
                },
                "availabilityViewInterval": 30
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/calendar/getSchedule",
                    headers=self.headers,
                    json=request_body,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Process schedule information
                availability = {}
                for schedule in data.get("value", []):
                    email = schedule.get("scheduleId")
                    busy_slots = []
                    
                    for item in schedule.get("scheduleItems", []):
                        if item.get("status") == "busy":
                            busy_slots.append({
                                "start": item.get("start", {}).get("dateTime"),
                                "end": item.get("end", {}).get("dateTime"),
                                "subject": item.get("subject", "Busy")
                            })
                    
                    availability[email] = busy_slots
                
                return availability
                
        except Exception as e:
            logger.error(f"Error getting calendar availability: {str(e)}")
            raise
    
    async def suggest_optimal_times(
        self,
        attendees: List[str],
        duration_minutes: int,
        preferred_days: Optional[List[str]] = None,
        preferred_hours: Optional[Tuple[int, int]] = None,
        timezone: str = "UTC",
        days_ahead: int = 14
    ) -> List[Dict[str, Any]]:
        """
        AI-powered suggestion of optimal meeting times based on preferences
        
        Args:
            attendees: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            preferred_days: Preferred days of week (e.g., ["Monday", "Wednesday"])
            preferred_hours: Preferred time range (e.g., (9, 17) for 9 AM to 5 PM)
            timezone: Timezone for the meeting
            days_ahead: Number of days to look ahead
        
        Returns:
            List of optimal time suggestions with AI confidence scores
        """
        try:
            # Calculate search window
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=days_ahead)
            
            # Get availability for all attendees
            availability = await self.get_calendar_availability(
                attendees,
                start_date,
                end_date,
                timezone
            )
            
            # Find free slots
            free_slots = self._find_free_slots(
                availability,
                start_date,
                end_date,
                duration_minutes,
                preferred_days,
                preferred_hours
            )
            
            # Score and rank slots using AI algorithm
            ranked_slots = self._rank_time_slots(
                free_slots,
                attendees,
                preferred_days,
                preferred_hours
            )
            
            return ranked_slots[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting optimal times: {str(e)}")
            raise
    
    def _enhance_suggestion(
        self,
        suggestion: Dict[str, Any],
        attendees: List[str],
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Enhance meeting time suggestion with additional metadata
        
        Args:
            suggestion: Raw suggestion from Graph API
            attendees: List of attendee emails
            duration_minutes: Meeting duration
        
        Returns:
            Enhanced suggestion with confidence score and reasoning
        """
        meeting_time = suggestion.get("meetingTimeSlot", {})
        confidence = suggestion.get("confidence", 0)
        
        # Calculate AI confidence score (0-100)
        ai_confidence = self._calculate_confidence_score(
            confidence,
            suggestion.get("suggestionReason", ""),
            len(attendees)
        )
        
        return {
            "start_time": meeting_time.get("start", {}).get("dateTime"),
            "end_time": meeting_time.get("end", {}).get("dateTime"),
            "confidence_score": ai_confidence,
            "attendee_availability": suggestion.get("attendeeAvailability", []),
            "suggestion_reason": suggestion.get("suggestionReason", ""),
            "organizer_availability": suggestion.get("organizerAvailability", "free"),
            "duration_minutes": duration_minutes
        }
    
    def _calculate_confidence_score(
        self,
        graph_confidence: float,
        reason: str,
        attendee_count: int
    ) -> float:
        """
        Calculate AI confidence score for a time slot
        
        Args:
            graph_confidence: Confidence from Graph API
            reason: Suggestion reason
            attendee_count: Number of attendees
        
        Returns:
            Confidence score (0-100)
        """
        # Base score from Graph API confidence
        base_score = graph_confidence * 100
        
        # Adjust based on reason
        reason_bonus = 0
        if "attendees available" in reason.lower():
            reason_bonus = 10
        elif "some attendees available" in reason.lower():
            reason_bonus = 5
        
        # Adjust based on attendee count (smaller meetings easier to schedule)
        if attendee_count <= 3:
            size_bonus = 5
        elif attendee_count <= 5:
            size_bonus = 3
        else:
            size_bonus = 0
        
        final_score = min(100, base_score + reason_bonus + size_bonus)
        return round(final_score, 2)
    
    def _find_free_slots(
        self,
        availability: Dict[str, List[Dict[str, Any]]],
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        preferred_days: Optional[List[str]] = None,
        preferred_hours: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find free time slots for all attendees
        
        Args:
            availability: Availability data for attendees
            start_date: Start of search window
            end_date: End of search window
            duration_minutes: Meeting duration
            preferred_days: Preferred days of week
            preferred_hours: Preferred time range
        
        Returns:
            List of free time slots
        """
        free_slots = []
        current = start_date
        slot_duration = timedelta(minutes=duration_minutes)
        
        # Default to business hours if not specified
        if preferred_hours is None:
            preferred_hours = (9, 17)  # 9 AM to 5 PM
        
        while current < end_date:
            # Skip weekends if preferred days specified
            if preferred_days and current.strftime("%A") not in preferred_days:
                current += timedelta(days=1)
                continue
            
            # Check business hours
            if current.hour < preferred_hours[0] or current.hour >= preferred_hours[1]:
                current += timedelta(hours=1)
                continue
            
            slot_end = current + slot_duration
            
            # Check if slot is free for all attendees
            is_free = True
            for email, busy_times in availability.items():
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                    busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                    
                    # Check for overlap
                    if not (slot_end <= busy_start or current >= busy_end):
                        is_free = False
                        break
                
                if not is_free:
                    break
            
            if is_free:
                free_slots.append({
                    "start_time": current,
                    "end_time": slot_end,
                    "duration_minutes": duration_minutes
                })
            
            # Move to next 30-minute slot
            current += timedelta(minutes=30)
        
        return free_slots
    
    def _rank_time_slots(
        self,
        slots: List[Dict[str, Any]],
        attendees: List[str],
        preferred_days: Optional[List[str]] = None,
        preferred_hours: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank time slots using AI scoring algorithm
        
        Args:
            slots: List of available time slots
            attendees: List of attendee emails
            preferred_days: Preferred days of week
            preferred_hours: Preferred time range
        
        Returns:
            Ranked list of time slots with confidence scores
        """
        scored_slots = []
        
        for slot in slots:
            score = 50.0  # Base score
            start_time = slot["start_time"]
            
            # Day preference bonus
            if preferred_days and start_time.strftime("%A") in preferred_days:
                score += 15
            
            # Time preference bonus
            if preferred_hours:
                hour = start_time.hour
                # Peak preference in middle of range
                mid_hour = (preferred_hours[0] + preferred_hours[1]) / 2
                hour_distance = abs(hour - mid_hour)
                time_bonus = max(0, 15 - hour_distance * 2)
                score += time_bonus
            
            # Avoid early morning or late evening
            if 10 <= start_time.hour <= 15:
                score += 10  # Prime meeting time
            elif start_time.hour < 9 or start_time.hour >= 17:
                score -= 10  # Less desirable
            
            # Avoid Monday mornings and Friday afternoons
            if start_time.strftime("%A") == "Monday" and start_time.hour < 10:
                score -= 5
            elif start_time.strftime("%A") == "Friday" and start_time.hour >= 15:
                score -= 5
            
            # Bonus for mid-week
            if start_time.strftime("%A") in ["Tuesday", "Wednesday", "Thursday"]:
                score += 5
            
            # Ensure score is within bounds
            score = max(0, min(100, score))
            
            scored_slots.append({
                "start_time": start_time.isoformat(),
                "end_time": slot["end_time"].isoformat(),
                "duration_minutes": slot["duration_minutes"],
                "confidence_score": round(score, 2),
                "attendee_count": len(attendees),
                "recommendation": self._get_recommendation(score)
            })
        
        # Sort by confidence score (descending)
        scored_slots.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return scored_slots
    
    def _get_recommendation(self, score: float) -> str:
        """
        Get recommendation text based on confidence score
        
        Args:
            score: Confidence score
        
        Returns:
            Recommendation text
        """
        if score >= 80:
            return "Highly recommended - optimal time for all attendees"
        elif score >= 65:
            return "Recommended - good time for most attendees"
        elif score >= 50:
            return "Acceptable - reasonable time slot"
        else:
            return "Available - consider alternative times if possible"


# Made with Bob