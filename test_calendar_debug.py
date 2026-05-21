"""
Debug script to test Google Calendar freebusy API
Run this to see what's actually being returned from Google Calendar
"""
import asyncio
import sys
from datetime import datetime, timedelta
from app.services.google_calendar_service import GoogleCalendarService
from app.db.database import get_db
from app.models.user import User
from sqlalchemy import select
from app.services.auth_service import auth_service

async def test_calendar():
    print("=" * 80)
    print("GOOGLE CALENDAR DEBUG TEST")
    print("=" * 80)
    
    # Get database session
    async for db in get_db():
        try:
            # Get the first user (you can modify this to get a specific user)
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No user found in database. Please login first.")
                return
            
            print(f"\n✓ Testing with user: {user.email}")
            print(f"  User ID: {user.id}")
            
            # Decrypt tokens
            if not user.access_token:
                print("❌ No access token found for user. Please login again.")
                return
            
            access_token = auth_service.decrypt_token(user.access_token)
            refresh_token = auth_service.decrypt_token(user.refresh_token) if user.refresh_token else None
            
            print(f"  Access token: {access_token[:20]}..." if access_token else "  No access token")
            
            # Create calendar service
            calendar_service = GoogleCalendarService(access_token, refresh_token)
            
            # Get user profile
            print("\n" + "=" * 80)
            print("STEP 1: Getting user profile")
            print("=" * 80)
            user_info = await calendar_service.get_user_profile()
            print(f"✓ User email from Google: {user_info.get('email')}")
            print(f"  Name: {user_info.get('name')}")
            
            # Test date range (today + next 7 days)
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=7)
            
            print("\n" + "=" * 80)
            print("STEP 2: Fetching calendar events")
            print("=" * 80)
            print(f"Date range: {start_time} to {end_time}")
            
            # Get calendar events
            events = await calendar_service.list_meetings(
                start_date=start_time,
                end_date=end_time,
                max_results=50
            )
            
            print(f"\n✓ Found {len(events)} events in your calendar:")
            for i, event in enumerate(events, 1):
                summary = event.get('summary', 'No title')
                start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                end = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                print(f"  {i}. {summary}")
                print(f"     Start: {start}")
                print(f"     End: {end}")
            
            # Test freebusy API
            print("\n" + "=" * 80)
            print("STEP 3: Testing FreeBusy API")
            print("=" * 80)
            
            # Ensure we have a valid email (not None)
            user_email = user_info.get('email')
            if not user_email:
                print("❌ Could not retrieve user email from Google profile")
                return
            
            test_emails = [user_email]
            print(f"Checking availability for: {test_emails}")
            
            freebusy_data = await calendar_service.get_free_busy(
                attendee_emails=test_emails,
                start_time=start_time,
                end_time=end_time,
                timezone='Asia/Kolkata'
            )
            
            print(f"\n✓ FreeBusy API Response:")
            calendars = freebusy_data.get('calendars', {})
            print(f"  Number of calendars returned: {len(calendars)}")
            
            for email, cal_data in calendars.items():
                busy_periods = cal_data.get('busy', [])
                errors = cal_data.get('errors', [])
                
                print(f"\n  Calendar: {email}")
                print(f"    Busy periods: {len(busy_periods)}")
                
                if errors:
                    print(f"    ⚠️ ERRORS: {errors}")
                
                for j, busy in enumerate(busy_periods, 1):
                    print(f"    {j}. {busy['start']} to {busy['end']}")
            
            # Test find_common_free_slots
            print("\n" + "=" * 80)
            print("STEP 4: Finding free slots")
            print("=" * 80)
            
            free_slots = await calendar_service.find_common_free_slots(
                attendee_emails=test_emails,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=30,
                timezone='Asia/Kolkata',
                working_hours_start=9,
                working_hours_end=17
            )
            
            print(f"\n✓ Found {len(free_slots)} free slots:")
            for i, slot in enumerate(free_slots[:10], 1):  # Show first 10
                print(f"  {i}. {slot['start_time']} to {slot['end_time']}")
                print(f"     Confidence: {slot['confidence_score']}%")
            
            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            
            # Check if any free slots overlap with busy periods
            if len(events) > 0 and len(free_slots) > 0:
                print("\n⚠️ CHECKING FOR OVERLAPS:")
                for event in events:
                    event_start = event.get('start', {}).get('dateTime')
                    event_end = event.get('end', {}).get('dateTime')
                    if event_start and event_end:
                        for slot in free_slots[:20]:
                            slot_start = slot['start_time']
                            slot_end = slot['end_time']
                            # Check for overlap
                            if not (slot_end <= event_start or slot_start >= event_end):
                                print(f"  ❌ OVERLAP FOUND!")
                                print(f"     Event: {event.get('summary')} ({event_start} to {event_end})")
                                print(f"     Free slot: {slot_start} to {slot_end}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Exit after processing first database session
        break

if __name__ == "__main__":
    asyncio.run(test_calendar())

# Made with Bob
