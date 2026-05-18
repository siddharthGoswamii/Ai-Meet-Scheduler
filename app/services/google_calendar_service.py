"""
Google Calendar API service for Google Meet and Calendar operations
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timezone
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
            body = {
                'timeMin': self._to_rfc3339(start_time),
                'timeMax': self._to_rfc3339(end_time),
                'timeZone': timezone,
                'items': [{'id': email} for email in attendee_emails]
            }
            
            freebusy_result = self.service.freebusy().query(body=body).execute()
            return freebusy_result
            
        except Exception as error:
            logger.error(f"Error getting free/busy info: {error}")
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