"""
Google Calendar API service for Google Meet and Calendar operations
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timezone, timedelta
import logging
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for interacting with Google Calendar API"""
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        """
        Initialize Google Calendar service with OAuth credentials.

        Args:
            access_token: User's access token for Google Calendar API.
            refresh_token: Optional user's refresh token for token renewal.
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.credentials = self._build_credentials()
        self.service = self._build_service('calendar', 'v3', credentials=self.credentials)
    
    @staticmethod
    def _import_google_module(module_name: str) -> Any:
        """
        Import a Google client module lazily.
        """
        import importlib

        return importlib.import_module(module_name)

    def _build_credentials(self) -> Any:
        """
        Build Google OAuth credentials.
        """
        credentials_module = self._import_google_module("google.oauth2.credentials")
        google_credentials = credentials_module.Credentials

        kwargs: Dict[str, Any] = {
            "token": self.access_token,
            "scopes": settings.google_scopes_list,
        }

        if self.refresh_token:
            kwargs["refresh_token"] = self.refresh_token
            kwargs["token_uri"] = "https://oauth2.googleapis.com/token"
            kwargs["client_id"] = settings.GOOGLE_CLIENT_ID
            kwargs["client_secret"] = settings.GOOGLE_CLIENT_SECRET

        return cast(Any, google_credentials(**kwargs))

    def _build_service(self, service_name: str, version: str, **kwargs: Any) -> Any:
        """
        Build a Google API service lazily.
        """
        discovery_module = self._import_google_module("googleapiclient.discovery")
        return discovery_module.build(service_name, version, **kwargs)

    @staticmethod
    def _to_rfc3339(value: datetime) -> str:
        """
        Convert a datetime to an RFC3339 timestamp expected by Google APIs.
        """
        if value.tzinfo is None:
            IST = timezone(timedelta(hours=5, minutes=30))
            value = value.replace(tzinfo=IST)
            return value.isoformat()

        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get user profile information from Google
        
        Returns:
            Dict containing user profile data
        """
        try:
            # Build OAuth2 API service for user info
            oauth_service = self._build_service('oauth2', 'v2', credentials=self.credentials)
            user_info = oauth_service.userinfo().get().execute()
            return user_info
        except Exception as error:
            logger.error(f"Error getting user profile: {error}")
            raise
    
    async def create_meeting(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        attendees: List[Dict[str, Any]],
        location: Optional[str] = None,
        is_online: bool = True
    ) -> Dict[str, Any]:
        """
        Create a Google Meet meeting via Calendar API
        
        Args:
            title: Meeting title
            description: Meeting description
            start_time: Meeting start time
            end_time: Meeting end time
            timezone: Timezone for the meeting
            attendees: List of attendee dictionaries
            location: Physical location (optional)
            is_online: Whether to create Google Meet link
        
        Returns:
            Dict containing created meeting data with Meet link
        """
        try:
            # Prepare attendees list
            google_attendees = []
            for attendee in attendees:
                google_attendees.append({
                    'email': attendee['email'],
                    'displayName': attendee.get('display_name', attendee['email']),
                    'responseStatus': 'needsAction'
                })
            
            # Prepare event data
            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
                'attendees': google_attendees,
                'reminders': {
                    'useDefault': True,
                },
            }
            
            # Add location if provided
            if location:
                event['location'] = location
            
            # Add Google Meet conference if online meeting
            if is_online:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1 if is_online else 0,
                sendUpdates='all'  # Send email invitations to all attendees
            ).execute()
            
            logger.info(f"Meeting created: {created_event.get('id')}")
            return created_event
            
        except Exception as error:
            logger.error(f"Error creating meeting: {error}")
            raise
    
    async def update_meeting(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing meeting
        
        Args:
            event_id: Google Calendar event ID
            updates: Dictionary of fields to update
        
        Returns:
            Dict containing updated meeting data
        """
        try:
            # Get existing event first
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            if 'title' in updates:
                event['summary'] = updates['title']
            
            if 'description' in updates:
                event['description'] = updates['description']
            
            if 'start_time' in updates and 'timezone' in updates:
                event['start'] = {
                    'dateTime': updates['start_time'].isoformat(),
                    'timeZone': updates['timezone']
                }
            
            if 'end_time' in updates and 'timezone' in updates:
                event['end'] = {
                    'dateTime': updates['end_time'].isoformat(),
                    'timeZone': updates['timezone']
                }
            
            if 'location' in updates:
                event['location'] = updates['location']
            
            if 'attendees' in updates:
                google_attendees = []
                for attendee in updates['attendees']:
                    google_attendees.append({
                        'email': attendee['email'],
                        'displayName': attendee.get('display_name', attendee['email'])
                    })
                event['attendees'] = google_attendees
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'  # Notify attendees of changes
            ).execute()
            
            logger.info(f"Meeting updated: {event_id}")
            return updated_event
            
        except Exception as error:
            logger.error(f"Error updating meeting: {error}")
            raise
    
    async def cancel_meeting(
        self,
        event_id: str,
        cancellation_message: Optional[str] = None
    ) -> None:
        """
        Cancel a meeting
        
        Args:
            event_id: Google Calendar event ID
            cancellation_message: Optional cancellation message
        """
        try:
            # Delete the event (sends cancellation to attendees)
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'  # Send cancellation to all attendees
            ).execute()
            
            logger.info(f"Meeting cancelled: {event_id}")
            
        except Exception as error:
            logger.error(f"Error cancelling meeting: {error}")
            raise
    
    async def get_meeting(self, event_id: str) -> Dict[str, Any]:
        """
        Get meeting details
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            Dict containing meeting data
        """
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return event
            
        except Exception as error:
            logger.error(f"Error getting meeting: {error}")
            raise
    
    async def list_meetings(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List user's meetings
        
        Args:
            start_date: Filter meetings starting from this date
            end_date: Filter meetings ending before this date
            max_results: Number of meetings to return
        
        Returns:
            List of meeting dictionaries
        """
        try:
            # Prepare parameters
            params = {
                'calendarId': 'primary',
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if start_date:
                params['timeMin'] = self._to_rfc3339(start_date)
            
            if end_date:
                params['timeMax'] = self._to_rfc3339(end_date)
            
            # Get events
            events_result = self.service.events().list(**params).execute()
            events = events_result.get('items', [])
            
            return events
            
        except Exception as error:
            logger.error(f"Error listing meetings: {error}")
            raise
    
    async def get_calendar_view(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get calendar view for a date range
        
        Args:
            start_date: Start date for calendar view
            end_date: End date for calendar view
        
        Returns:
            List of events in the date range
        """
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=self._to_rfc3339(start_date),
                timeMax=self._to_rfc3339(end_date),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except Exception as error:
            logger.error(f"Error getting calendar view: {error}")
            raise
    
    async def get_free_busy(
        self,
        attendee_emails: List[str],
        start_time: datetime,
        end_time: datetime,
        timezone: str = 'UTC'
    ) -> Dict[str, Any]:
        """
        Get free/busy information for attendees
        
        Args:
            attendee_emails: List of attendee email addresses
            start_time: Start time for availability check
            end_time: End time for availability check
            timezone: Timezone for the query
        
        Returns:
            Dict containing free/busy information
        """
        try:
            # Get user's email to include their calendar
            user_info = await self.get_user_profile()
            user_email = user_info.get('email')
            
            # Ensure user's email is in the list (to check their own calendar)
            all_emails = list(set(attendee_emails + ([user_email] if user_email else [])))
            
            body = {
                'timeMin': self._to_rfc3339(start_time),
                'timeMax': self._to_rfc3339(end_time),
                'timeZone': timezone,
                'items': [{'id': email} for email in all_emails]
            }
            
            logger.info(f"Fetching freebusy for emails: {all_emails}")
            logger.info(f"Time range: {self._to_rfc3339(start_time)} to {self._to_rfc3339(end_time)}")
            
            freebusy_result = self.service.freebusy().query(body=body).execute()
            
            logger.info(f"Freebusy response received for {len(freebusy_result.get('calendars', {}))} calendars")
            
            # Log each calendar's busy periods for debugging
            for email, cal_data in freebusy_result.get('calendars', {}).items():
                busy_count = len(cal_data.get('busy', []))
                logger.info(f"Calendar {email}: {busy_count} busy periods")
                if busy_count > 0:
                    logger.info(f"  Busy periods: {cal_data.get('busy', [])}")
            
            return freebusy_result
            
        except Exception as error:
            logger.error(f"Error getting free/busy info: {error}")
            raise
    
    async def find_common_free_slots(
        self,
        attendee_emails: List[str],
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        timezone: str = 'UTC',
        working_hours_start: int = 9,
        working_hours_end: int = 17
    ) -> List[Dict[str, Any]]:
        """
        Find time slots when all attendees are free
        
        Args:
            attendee_emails: List of attendee email addresses
            start_time: Start of search window
            end_time: End of search window
            duration_minutes: Required meeting duration in minutes
            timezone: Timezone for the search
            working_hours_start: Start of working hours (default 9 AM)
            working_hours_end: End of working hours (default 5 PM)
        
        Returns:
            List of available time slots with confidence scores
        """
        try:
            # Get free/busy information for all attendees
            freebusy_data = await self.get_free_busy(
                attendee_emails,
                start_time,
                end_time,
                timezone
            )
            
            # Extract busy periods for each attendee
            all_busy_periods = []
            calendars = freebusy_data.get('calendars', {})
            
            # Check ALL calendars returned (including user's own calendar)
            logger.info(f"Processing busy periods from {len(calendars)} calendars")
            for email, calendar_data in calendars.items():
                busy_periods = calendar_data.get('busy', [])
                logger.info(f"Calendar {email} has {len(busy_periods)} busy periods")
                
                for busy in busy_periods:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    all_busy_periods.append({
                        'start': busy_start,
                        'end': busy_end,
                        'email': email
                    })
                    logger.info(f"  Busy: {busy_start} to {busy_end}")
            
            # Sort busy periods by start time
            all_busy_periods.sort(key=lambda x: x['start'])
            logger.info(f"Total busy periods to check: {len(all_busy_periods)}")
            
            # Find free slots
            free_slots = []
            current_time = start_time
            slot_duration = timedelta(minutes=duration_minutes)
            
            while current_time + slot_duration <= end_time:
                # Skip non-working hours
                if current_time.hour < working_hours_start or current_time.hour >= working_hours_end:
                    # Move to next working hour
                    if current_time.hour < working_hours_start:
                        current_time = current_time.replace(hour=working_hours_start, minute=0, second=0)
                    else:
                        current_time = (current_time + timedelta(days=1)).replace(
                            hour=working_hours_start, minute=0, second=0
                        )
                    continue
                
                # Skip weekends
                if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    current_time = (current_time + timedelta(days=1)).replace(
                        hour=working_hours_start, minute=0, second=0
                    )
                    continue
                
                slot_end = current_time + slot_duration
                
                # Check if this slot conflicts with any busy period
                is_free = True
                for busy in all_busy_periods:
                    # Check for overlap
                    if not (slot_end <= busy['start'] or current_time >= busy['end']):
                        is_free = False
                        # Jump to end of this busy period
                        current_time = busy['end']
                        break
                
                if is_free:
                    # Calculate confidence score based on time of day and day of week
                    confidence = self._calculate_slot_confidence(
                        current_time,
                        duration_minutes,
                        len(attendee_emails)
                    )
                    
                    free_slots.append({
                        'start_time': current_time.isoformat(),
                        'end_time': slot_end.isoformat(),
                        'duration_minutes': duration_minutes,
                        'confidence_score': confidence,
                        'attendee_count': len(attendee_emails),
                        'day_of_week': current_time.strftime('%A'),
                        'time_of_day': current_time.strftime('%I:%M %p')
                    })
                    logger.debug(f"Free slot found: {current_time.isoformat()} to {slot_end.isoformat()}")
                    
                    # Move to next 15-minute slot
                    current_time += timedelta(minutes=15)
                # else: Already moved to end of busy period in the conflict check above
            
            # Sort by confidence score (highest first)
            free_slots.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            logger.info(f"Found {len(free_slots)} free slots for {len(attendee_emails)} attendees")
            return free_slots
            
        except Exception as error:
            logger.error(f"Error finding common free slots: {error}")
            raise
    
    def _calculate_slot_confidence(
        self,
        slot_time: datetime,
        duration_minutes: int,
        attendee_count: int
    ) -> float:
        """
        Calculate confidence score for a time slot based on various factors
        
        Args:
            slot_time: Start time of the slot
            duration_minutes: Duration of the meeting
            attendee_count: Number of attendees
        
        Returns:
            Confidence score (0-100)
        """
        score = 50.0  # Base score
        
        # Time of day scoring (prefer mid-morning and early afternoon)
        hour = slot_time.hour
        if 10 <= hour <= 11 or 14 <= hour <= 15:
            score += 20  # Prime meeting times
        elif 9 <= hour <= 10 or 13 <= hour <= 14 or 15 <= hour <= 16:
            score += 10  # Good meeting times
        elif hour < 9 or hour >= 17:
            score -= 15  # Less desirable times
        
        # Day of week scoring
        day = slot_time.weekday()
        if day in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
            score += 10  # Best days for meetings
        elif day == 0:  # Monday
            if hour < 10:
                score -= 10  # Avoid Monday mornings
            else:
                score += 5
        elif day == 4:  # Friday
            if hour >= 15:
                score -= 10  # Avoid Friday afternoons
            else:
                score += 5
        
        # Duration scoring (shorter meetings are easier to schedule)
        if duration_minutes <= 30:
            score += 5
        elif duration_minutes >= 120:
            score -= 5
        
        # Attendee count scoring (fewer attendees = higher confidence)
        if attendee_count <= 3:
            score += 10
        elif attendee_count <= 5:
            score += 5
        elif attendee_count >= 10:
            score -= 5
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return round(score, 2)
    
    async def auto_schedule_meeting(
        self,
        title: str,
        description: str,
        attendee_emails: List[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        timezone: str = 'UTC',
        working_hours_start: int = 9,
        working_hours_end: int = 17,
        location: Optional[str] = None,
        is_online: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically find the best time and schedule a meeting
        
        Args:
            title: Meeting title
            description: Meeting description
            attendee_emails: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            start_date: Start of search window
            end_date: End of search window
            timezone: Timezone for the meeting
            working_hours_start: Start of working hours
            working_hours_end: End of working hours
            location: Physical location (optional)
            is_online: Whether to create Google Meet link
        
        Returns:
            Dict containing created meeting data with selected time slot info
        """
        try:
            # Find available time slots
            free_slots = await self.find_common_free_slots(
                attendee_emails,
                start_date,
                end_date,
                duration_minutes,
                timezone,
                working_hours_start,
                working_hours_end
            )
            
            if not free_slots:
                raise ValueError("No available time slots found for all attendees")
            
            # Select the best time slot (highest confidence)
            best_slot = free_slots[0]
            
            # Parse the selected time
            selected_start = datetime.fromisoformat(best_slot['start_time'])
            selected_end = datetime.fromisoformat(best_slot['end_time'])
            
            # Prepare attendees list
            attendees = [{'email': email} for email in attendee_emails]
            
            # Create the meeting
            meeting = await self.create_meeting(
                title=title,
                description=description,
                start_time=selected_start,
                end_time=selected_end,
                timezone=timezone,
                attendees=attendees,
                location=location,
                is_online=is_online
            )
            
            # Add scheduling metadata to response
            meeting['scheduling_info'] = {
                'selected_slot': best_slot,
                'total_slots_found': len(free_slots),
                'alternative_slots': free_slots[1:6] if len(free_slots) > 1 else [],
                'scheduling_method': 'AI-powered Google Calendar analysis'
            }
            
            logger.info(f"Auto-scheduled meeting '{title}' at {best_slot['start_time']} with confidence {best_slot['confidence_score']}%")
            
            return meeting
            
        except Exception as error:
            logger.error(f"Error auto-scheduling meeting: {error}")
            raise
    
    def extract_meet_link(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Extract Google Meet link from event
        
        Args:
            event: Google Calendar event dictionary
        
        Returns:
            Google Meet link URL or None
        """
        if 'conferenceData' in event:
            entry_points = event['conferenceData'].get('entryPoints', [])
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    return entry_point.get('uri')
        
        # Fallback: check hangoutLink
        return event.get('hangoutLink')


# Made with Bob