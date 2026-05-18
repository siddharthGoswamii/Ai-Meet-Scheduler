"""
AI Scheduling System - Usage Examples

This file demonstrates how to use the AI-powered meeting scheduling system.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any


class AISchedulingClient:
    """Client for interacting with AI Scheduling API"""
    
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def find_meeting_times(
        self,
        attendees: List[str],
        duration_minutes: int,
        days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Find optimal meeting times using Microsoft Graph AI
        
        Example:
            client = AISchedulingClient(base_url, token)
            result = await client.find_meeting_times(
                attendees=["alice@company.com", "bob@company.com"],
                duration_minutes=60
            )
        """
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/ai-scheduling/find-meeting-times",
                headers=self.headers,
                json={
                    "attendees": attendees,
                    "duration_minutes": duration_minutes,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timezone": "UTC",
                    "min_attendee_percentage": 100.0,
                    "max_suggestions": 10
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def suggest_optimal_times(
        self,
        attendees: List[str],
        duration_minutes: int,
        preferred_days: List[str] = None,
        preferred_start_hour: int = 9,
        preferred_end_hour: int = 17,
        days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Get AI-powered optimal time suggestions with preferences
        
        Example:
            result = await client.suggest_optimal_times(
                attendees=["alice@company.com", "bob@company.com"],
                duration_minutes=30,
                preferred_days=["Tuesday", "Wednesday", "Thursday"],
                preferred_start_hour=10,
                preferred_end_hour=16
            )
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/ai-scheduling/suggest-optimal-times",
                headers=self.headers,
                json={
                    "attendees": attendees,
                    "duration_minutes": duration_minutes,
                    "preferred_days": preferred_days,
                    "preferred_start_hour": preferred_start_hour,
                    "preferred_end_hour": preferred_end_hour,
                    "timezone": "UTC",
                    "days_ahead": days_ahead
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_calendar_availability(
        self,
        attendee_emails: List[str],
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Get detailed calendar availability for attendees
        
        Example:
            result = await client.get_calendar_availability(
                attendee_emails=["alice@company.com", "bob@company.com"],
                days_ahead=7
            )
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=days_ahead)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/ai-scheduling/calendar-availability",
                headers=self.headers,
                json={
                    "attendee_emails": attendee_emails,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "timezone": "UTC"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def auto_schedule_meeting(
        self,
        title: str,
        attendees: List[str],
        duration_minutes: int,
        description: str = None,
        preferred_days: List[str] = None,
        preferred_start_hour: int = 9,
        preferred_end_hour: int = 17,
        auto_select: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically schedule a meeting at the best available time
        
        Example:
            result = await client.auto_schedule_meeting(
                title="Team Sync",
                attendees=["alice@company.com", "bob@company.com"],
                duration_minutes=30,
                preferred_days=["Tuesday", "Wednesday"],
                auto_select=True
            )
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/ai-scheduling/auto-schedule",
                headers=self.headers,
                json={
                    "title": title,
                    "description": description,
                    "attendees": attendees,
                    "duration_minutes": duration_minutes,
                    "preferred_days": preferred_days,
                    "preferred_start_hour": preferred_start_hour,
                    "preferred_end_hour": preferred_end_hour,
                    "timezone": "UTC",
                    "days_ahead": 14,
                    "is_online": True,
                    "auto_select_best_time": auto_select
                }
            )
            response.raise_for_status()
            return response.json()


# Example Usage Scenarios

async def example_1_quick_auto_schedule():
    """
    Example 1: Quick Auto-Schedule
    Automatically find and schedule a meeting at the best time
    """
    print("=== Example 1: Quick Auto-Schedule ===\n")
    
    client = AISchedulingClient(
        base_url="http://localhost:8000",
        access_token="your_access_token_here"
    )
    
    result = await client.auto_schedule_meeting(
        title="Weekly Team Sync",
        attendees=[
            "alice@company.com",
            "bob@company.com",
            "charlie@company.com"
        ],
        duration_minutes=30,
        description="Weekly team synchronization meeting",
        preferred_days=["Tuesday", "Wednesday", "Thursday"],
        preferred_start_hour=10,
        preferred_end_hour=16,
        auto_select=True
    )
    
    if result["status"] == "scheduled":
        print(f"✓ Meeting scheduled successfully!")
        print(f"  Meeting ID: {result['meeting_id']}")
        print(f"  Time: {result['selected_time']['start_time']}")
        print(f"  Confidence: {result['selected_time']['confidence_score']}%")
        print(f"  {result['message']}\n")
        
        if result.get("alternative_times"):
            print(f"Alternative times available: {len(result['alternative_times'])}")
    else:
        print(f"✗ Could not schedule: {result['message']}")


async def example_2_review_suggestions_first():
    """
    Example 2: Review Suggestions Before Scheduling
    Get AI suggestions, review them, then schedule manually
    """
    print("=== Example 2: Review Suggestions First ===\n")
    
    client = AISchedulingClient(
        base_url="http://localhost:8000",
        access_token="your_access_token_here"
    )
    
    # Step 1: Get suggestions
    suggestions = await client.suggest_optimal_times(
        attendees=["alice@company.com", "bob@company.com"],
        duration_minutes=60,
        preferred_days=["Monday", "Wednesday", "Friday"],
        preferred_start_hour=9,
        preferred_end_hour=17,
        days_ahead=7
    )
    
    print(f"Found {suggestions['total_suggestions']} suggestions:\n")
    
    # Display top 3 suggestions
    for i, slot in enumerate(suggestions['suggestions'][:3], 1):
        print(f"{i}. {slot['start_time']}")
        print(f"   Confidence: {slot['confidence_score']}%")
        print(f"   {slot['recommendation']}\n")
    
    # AI Analysis
    analysis = suggestions['ai_analysis']
    print(f"AI Analysis:")
    print(f"  Average Confidence: {analysis['average_confidence']}%")
    print(f"  Best Time: {analysis['best_time']}")
    print(f"  Method: {analysis['analysis_method']}\n")


async def example_3_check_availability_first():
    """
    Example 3: Check Availability Before Scheduling
    Useful for large groups or important meetings
    """
    print("=== Example 3: Check Availability First ===\n")
    
    client = AISchedulingClient(
        base_url="http://localhost:8000",
        access_token="your_access_token_here"
    )
    
    attendees = [
        "alice@company.com",
        "bob@company.com",
        "charlie@company.com",
        "diana@company.com"
    ]
    
    # Check availability for next week
    availability = await client.get_calendar_availability(
        attendee_emails=attendees,
        days_ahead=7
    )
    
    print(f"Availability Analysis for {len(attendees)} attendees:\n")
    print(f"Overall Availability: {availability['overall_availability']}%\n")
    
    for attendee in availability['attendees']:
        print(f"{attendee['email']}:")
        print(f"  Available: {attendee['availability_percentage']}%")
        print(f"  Busy slots: {len(attendee['busy_slots'])}")
        print(f"  Total busy time: {attendee['total_busy_minutes']} minutes\n")
    
    # Decide whether to proceed
    if availability['overall_availability'] > 70:
        print("✓ Good availability - proceeding with scheduling...")
        # Proceed with auto-scheduling
    else:
        print("⚠ Low availability - consider different dates or fewer attendees")


async def example_4_microsoft_graph_integration():
    """
    Example 4: Using Microsoft Graph findMeetingTimes
    Leverages Microsoft's AI for meeting scheduling
    """
    print("=== Example 4: Microsoft Graph Integration ===\n")
    
    client = AISchedulingClient(
        base_url="http://localhost:8000",
        access_token="your_access_token_here"
    )
    
    result = await client.find_meeting_times(
        attendees=[
            "alice@company.com",
            "bob@company.com",
            "charlie@company.com"
        ],
        duration_minutes=45,
        days_ahead=14
    )
    
    print(f"Microsoft Graph AI found {result['total_suggestions']} suggestions:\n")
    
    for i, suggestion in enumerate(result['suggestions'][:5], 1):
        print(f"{i}. {suggestion['start_time']} - {suggestion['end_time']}")
        print(f"   Confidence: {suggestion['confidence_score']}%")
        print(f"   Reason: {suggestion['suggestion_reason']}")
        print(f"   Organizer: {suggestion['organizer_availability']}")
        
        # Show attendee availability
        available = sum(1 for a in suggestion['attendee_availability'] 
                       if a['availability'] == 'free')
        total = len(suggestion['attendee_availability'])
        print(f"   Attendees available: {available}/{total}\n")


async def example_5_smart_scheduling_workflow():
    """
    Example 5: Complete Smart Scheduling Workflow
    Demonstrates a full workflow with error handling
    """
    print("=== Example 5: Smart Scheduling Workflow ===\n")
    
    client = AISchedulingClient(
        base_url="http://localhost:8000",
        access_token="your_access_token_here"
    )
    
    attendees = ["alice@company.com", "bob@company.com"]
    
    try:
        # Step 1: Check availability
        print("Step 1: Checking availability...")
        availability = await client.get_calendar_availability(
            attendee_emails=attendees,
            days_ahead=7
        )
        
        if availability['overall_availability'] < 50:
            print("⚠ Low availability detected. Extending search window...")
            availability = await client.get_calendar_availability(
                attendee_emails=attendees,
                days_ahead=14
            )
        
        print(f"✓ Overall availability: {availability['overall_availability']}%\n")
        
        # Step 2: Get AI suggestions
        print("Step 2: Getting AI-powered suggestions...")
        suggestions = await client.suggest_optimal_times(
            attendees=attendees,
            duration_minutes=30,
            preferred_days=["Tuesday", "Wednesday", "Thursday"],
            preferred_start_hour=10,
            preferred_end_hour=16
        )
        
        if not suggestions['suggestions']:
            print("✗ No suitable times found")
            return
        
        best_suggestion = suggestions['suggestions'][0]
        print(f"✓ Best time found: {best_suggestion['start_time']}")
        print(f"  Confidence: {best_suggestion['confidence_score']}%\n")
        
        # Step 3: Auto-schedule if confidence is high
        if best_suggestion['confidence_score'] >= 75:
            print("Step 3: Auto-scheduling (high confidence)...")
            result = await client.auto_schedule_meeting(
                title="Project Discussion",
                attendees=attendees,
                duration_minutes=30,
                description="Discussing project milestones",
                preferred_days=["Tuesday", "Wednesday", "Thursday"],
                auto_select=True
            )
            
            if result['status'] == 'scheduled':
                print(f"✓ Meeting scheduled successfully!")
                print(f"  Meeting ID: {result['meeting_id']}")
                print(f"  {result['message']}")
            else:
                print(f"✗ Scheduling failed: {result['message']}")
        else:
            print("Step 3: Manual review recommended (lower confidence)")
            print("Please review suggestions and schedule manually.")
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def main():
    """Run all examples"""
    print("AI-Powered Meeting Scheduling - Examples\n")
    print("=" * 60 + "\n")
    
    # Note: Replace with actual access token before running
    print("Note: Update access_token in each example before running\n")
    print("=" * 60 + "\n")
    
    # Uncomment to run specific examples:
    # await example_1_quick_auto_schedule()
    # await example_2_review_suggestions_first()
    # await example_3_check_availability_first()
    # await example_4_microsoft_graph_integration()
    # await example_5_smart_scheduling_workflow()
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())


# Made with Bob