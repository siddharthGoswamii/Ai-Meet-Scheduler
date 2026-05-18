"""
Microsoft Graph API service for Teams and Calendar operations
"""
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphAPIService:
    """Service for interacting with Microsoft Graph API"""
    
    def __init__(self, access_token: str):
        """
        Initialize Graph API service with access token
        
        Args:
            access_token: User's access token for Microsoft Graph API
        """
        self.access_token = access_token
        self.base_url = settings.GRAPH_API_ENDPOINT
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get user profile information
        
        Returns:
            Dict containing user profile data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
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
        Create a Teams meeting via Graph API
        
        Args:
            title: Meeting title
            description: Meeting description
            start_time: Meeting start time
            end_time: Meeting end time
            timezone: Timezone for the meeting
            attendees: List of attendee dictionaries
            location: Physical location (optional)
            is_online: Whether to create online meeting link
        
        Returns:
            Dict containing created meeting data
        """
        # Prepare attendees list
        graph_attendees = []
        for attendee in attendees:
            graph_attendees.append({
                "emailAddress": {
                    "address": attendee["email"],
                    "name": attendee.get("display_name", attendee["email"])
                },
                "type": "required" if attendee.get("is_required", True) else "optional"
            })
        
        # Prepare meeting data
        meeting_data = {
            "subject": title,
            "body": {
                "contentType": "HTML",
                "content": description or ""
            },
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": timezone
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": timezone
            },
            "attendees": graph_attendees,
            "isOnlineMeeting": is_online,
            "onlineMeetingProvider": "teamsForBusiness" if is_online else None
        }
        
        # Add location if provided
        if location:
            meeting_data["location"] = {
                "displayName": location
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/events",
                headers=self.headers,
                json=meeting_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def update_meeting(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing meeting
        
        Args:
            event_id: Microsoft Graph event ID
            updates: Dictionary of fields to update
        
        Returns:
            Dict containing updated meeting data
        """
        # Prepare update data
        update_data = {}
        
        if "title" in updates:
            update_data["subject"] = updates["title"]
        
        if "description" in updates:
            update_data["body"] = {
                "contentType": "HTML",
                "content": updates["description"]
            }
        
        if "start_time" in updates and "timezone" in updates:
            update_data["start"] = {
                "dateTime": updates["start_time"].isoformat(),
                "timeZone": updates["timezone"]
            }
        
        if "end_time" in updates and "timezone" in updates:
            update_data["end"] = {
                "dateTime": updates["end_time"].isoformat(),
                "timeZone": updates["timezone"]
            }
        
        if "location" in updates:
            update_data["location"] = {
                "displayName": updates["location"]
            }
        
        if "attendees" in updates:
            graph_attendees = []
            for attendee in updates["attendees"]:
                graph_attendees.append({
                    "emailAddress": {
                        "address": attendee["email"],
                        "name": attendee.get("display_name", attendee["email"])
                    },
                    "type": "required" if attendee.get("is_required", True) else "optional"
                })
            update_data["attendees"] = graph_attendees
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/me/events/{event_id}",
                headers=self.headers,
                json=update_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def cancel_meeting(
        self,
        event_id: str,
        cancellation_message: Optional[str] = None
    ) -> None:
        """
        Cancel a meeting
        
        Args:
            event_id: Microsoft Graph event ID
            cancellation_message: Optional cancellation message
        """
        cancel_data = {
            "comment": cancellation_message or "Meeting cancelled"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/events/{event_id}/cancel",
                headers=self.headers,
                json=cancel_data,
                timeout=30.0
            )
            response.raise_for_status()
    
    async def get_meeting(self, event_id: str) -> Dict[str, Any]:
        """
        Get meeting details
        
        Args:
            event_id: Microsoft Graph event ID
        
        Returns:
            Dict containing meeting data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/events/{event_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def list_meetings(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        top: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List user's meetings
        
        Args:
            start_date: Filter meetings starting from this date
            end_date: Filter meetings ending before this date
            top: Number of meetings to return
        
        Returns:
            List of meeting dictionaries
        """
        params = {
            "$top": top,
            "$orderby": "start/dateTime"
        }
        
        # Add date filters if provided
        filters = []
        if start_date:
            filters.append(f"start/dateTime ge '{start_date.isoformat()}'")
        if end_date:
            filters.append(f"end/dateTime le '{end_date.isoformat()}'")
        
        if filters:
            params["$filter"] = " and ".join(filters)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])
    
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
        params = {
            "startDateTime": start_date.isoformat(),
            "endDateTime": end_date.isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/calendarView",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])

# Made with Bob
