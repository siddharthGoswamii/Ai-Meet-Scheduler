"""
AI-powered meeting scheduler service - Google Calendar version
"""
import httpx
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AISchedulerService:

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_calendar_availability(
        self,
        attendee_emails: List[str],
        start_time: datetime,
        end_time: datetime,
        timezone: str = "UTC"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get busy times from Google Calendar FreeBusy API"""
        try:
            # First, get the current user's email to include their calendar
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=self.headers,
                    timeout=30.0
                )
                user_response.raise_for_status()
                user_info = user_response.json()
                user_email = user_info.get('email')
            
            # Include user's email in the list (avoid duplicates)
            all_emails = list(set(attendee_emails + ([user_email] if user_email else [])))
            logger.info(f"Fetching calendar availability for: {all_emails}")
            
            request_body = {
                "timeMin": start_time.isoformat() + "Z",
                "timeMax": end_time.isoformat() + "Z",
                "timeZone": timezone,
                "items": [{"id": email} for email in all_emails]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.googleapis.com/calendar/v3/freeBusy",
                    headers=self.headers,
                    json=request_body,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            availability = {}
            calendars = data.get("calendars", {})
            
            # Process ALL calendars returned (including user's own)
            for email, cal_data in calendars.items():
                busy_slots = []
                for slot in cal_data.get("busy", []):
                    busy_slots.append({
                        "start": slot["start"],
                        "end":   slot["end"],
                        "subject": "Busy"
                    })
                availability[email] = busy_slots
                logger.info(f"Calendar {email}: {len(busy_slots)} busy periods found")

            return availability

        except Exception as e:
            logger.error(f"Error getting calendar availability: {str(e)}")
            raise

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
        Find optimal meeting times for Google Calendar
        
        Args:
            attendees: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            start_date: Start of search window
            end_date: End of search window
            timezone: Timezone for the meeting
            min_attendee_percentage: Minimum percentage of attendees required (not used in Google Calendar)
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of suggested meeting time slots with confidence scores
        """
        try:
            availability = await self.get_calendar_availability(
                attendees, start_date, end_date, timezone
            )

            free_slots = self._find_free_slots(
                availability, start_date, end_date,
                duration_minutes, None, None
            )

            ranked = self._rank_time_slots(
                free_slots, attendees, None, None
            )

            # Format results to match expected output structure
            suggestions = []
            for slot in ranked[:max_suggestions]:
                suggestions.append({
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "confidence_score": slot["confidence_score"],
                    "attendee_availability": [
                        {
                            "attendee": {"emailAddress": {"address": email}},
                            "availability": "free"
                        }
                        for email in attendees
                    ],
                    "suggestion_reason": slot["recommendation"],
                    "organizer_availability": "free",
                    "duration_minutes": duration_minutes
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error finding meeting times: {str(e)}")
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
        """Find and rank free slots for all attendees"""
        try:
            start_date = datetime.utcnow()
            end_date   = start_date + timedelta(days=days_ahead)

            availability = await self.get_calendar_availability(
                attendees, start_date, end_date, timezone
            )

            free_slots = self._find_free_slots(
                availability, start_date, end_date,
                duration_minutes, preferred_days, preferred_hours
            )

            ranked = self._rank_time_slots(
                free_slots, attendees, preferred_days, preferred_hours
            )

            return ranked[:10]

        except Exception as e:
            logger.error(f"Error suggesting optimal times: {str(e)}")
            raise

    def _find_free_slots(
        self,
        availability: Dict[str, List[Dict[str, Any]]],
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        preferred_days: Optional[List[str]] = None,
        preferred_hours: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:

        free_slots    = []
        current       = start_date.replace(minute=0, second=0, microsecond=0)
        slot_duration = timedelta(minutes=duration_minutes)

        if preferred_hours is None:
            preferred_hours = (9, 17)

        while current < end_date:
            if current.weekday() >= 5:  # skip weekends
                current += timedelta(days=1)
                current = current.replace(hour=preferred_hours[0])
                continue

            if current.hour < preferred_hours[0]:
                current = current.replace(hour=preferred_hours[0])
                continue

            if current.hour >= preferred_hours[1]:
                current += timedelta(days=1)
                current = current.replace(hour=preferred_hours[0])
                continue

            slot_end = current + slot_duration
            is_free  = True

            for email, busy_times in availability.items():
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy["start"].replace("Z", ""))
                    busy_end   = datetime.fromisoformat(busy["end"].replace("Z", ""))
                    if not (slot_end <= busy_start or current >= busy_end):
                        is_free = False
                        break
                if not is_free:
                    break

            if is_free:
                free_slots.append({
                    "start_time":      current,
                    "end_time":        slot_end,
                    "duration_minutes": duration_minutes
                })

            current += timedelta(minutes=30)

        return free_slots

    def _rank_time_slots(
        self,
        slots: List[Dict[str, Any]],
        attendees: List[str],
        preferred_days: Optional[List[str]] = None,
        preferred_hours: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:

        scored = []
        for slot in slots:
            score      = 50.0
            start_time = slot["start_time"]

            if preferred_days and start_time.strftime("%A") in preferred_days:
                score += 15

            if preferred_hours:
                mid        = (preferred_hours[0] + preferred_hours[1]) / 2
                score     += max(0, 15 - abs(start_time.hour - mid) * 2)

            if 10 <= start_time.hour <= 15:
                score += 10
            if start_time.strftime("%A") in ["Tuesday", "Wednesday", "Thursday"]:
                score += 5
            if start_time.strftime("%A") == "Monday" and start_time.hour < 10:
                score -= 5
            if start_time.strftime("%A") == "Friday" and start_time.hour >= 15:
                score -= 5

            score = max(0, min(100, score))

            scored.append({
                "start_time":       start_time.isoformat(),
                "end_time":         slot["end_time"].isoformat(),
                "duration_minutes": slot["duration_minutes"],
                "confidence_score": round(score, 2),
                "attendee_count":   len(attendees),
                "recommendation":   self._get_recommendation(score)
            })

        scored.sort(key=lambda x: x["confidence_score"], reverse=True)
        return scored

    def _get_recommendation(self, score: float) -> str:
        if score >= 80:
            return "Highly recommended - optimal time for all attendees"
        elif score >= 65:
            return "Recommended - good time for most attendees"
        elif score >= 50:
            return "Acceptable - reasonable time slot"
        return "Available - consider alternative times if possible"