# AI-Powered Meeting Scheduler - Google Calendar Integration

## Overview

This application now includes advanced AI-powered scheduling features that automatically find the best meeting times by checking all attendees' Google Calendars. The system analyzes availability, applies intelligent scoring algorithms, and automatically schedules meetings when everyone is free.

## Key Features

### 1. **Multi-Attendee Availability Check**
- Checks Google Calendar availability for all attendees simultaneously
- Uses Google Calendar's Free/Busy API for real-time availability data
- Respects working hours and business days

### 2. **AI-Powered Time Slot Ranking**
- Intelligent scoring algorithm considers:
  - Time of day (prefers mid-morning and early afternoon)
  - Day of week (prefers Tuesday-Thursday)
  - Meeting duration
  - Number of attendees
  - Avoids Monday mornings and Friday afternoons

### 3. **Automatic Meeting Scheduling**
- Finds the best available time slot
- Creates Google Calendar event with Google Meet link
- Sends invitations to all attendees automatically
- Provides alternative time slots if needed

## API Endpoints

### 1. Find Free Time Slots

**Endpoint:** `POST /calendar/find-free-slots`

Finds all available time slots when all attendees are free.

**Request Body:**
```json
{
  "attendee_emails": [
    "attendee1@example.com",
    "attendee2@example.com",
    "attendee3@example.com"
  ],
  "duration_minutes": 60,
  "start_date": "2026-05-20T00:00:00Z",
  "end_date": "2026-05-27T23:59:59Z",
  "timezone": "Asia/Kolkata",
  "working_hours_start": 9,
  "working_hours_end": 17
}
```

**Response:**
```json
{
  "free_slots": [
    {
      "start_time": "2026-05-21T10:00:00+05:30",
      "end_time": "2026-05-21T11:00:00+05:30",
      "duration_minutes": 60,
      "confidence_score": 85.0,
      "attendee_count": 3,
      "day_of_week": "Wednesday",
      "time_of_day": "10:00 AM"
    },
    {
      "start_time": "2026-05-22T14:00:00+05:30",
      "end_time": "2026-05-22T15:00:00+05:30",
      "duration_minutes": 60,
      "confidence_score": 80.0,
      "attendee_count": 3,
      "day_of_week": "Thursday",
      "time_of_day": "02:00 PM"
    }
  ],
  "total_slots": 15,
  "search_window": {
    "start_date": "2026-05-20T00:00:00Z",
    "end_date": "2026-05-27T23:59:59Z",
    "timezone": "Asia/Kolkata",
    "attendee_count": 3
  },
  "message": "Found 15 available time slots for 3 attendees"
}
```

### 2. Auto-Schedule Meeting

**Endpoint:** `POST /calendar/auto-schedule`

Automatically schedules a meeting at the best available time.

**Request Body:**
```json
{
  "title": "Team Sync Meeting",
  "description": "Weekly team synchronization meeting",
  "attendee_emails": [
    "attendee1@example.com",
    "attendee2@example.com",
    "attendee3@example.com"
  ],
  "duration_minutes": 60,
  "start_date": "2026-05-20T00:00:00Z",
  "end_date": "2026-05-27T23:59:59Z",
  "timezone": "Asia/Kolkata",
  "working_hours_start": 9,
  "working_hours_end": 17,
  "location": "Conference Room A",
  "is_online": true
}
```

**Response:**
```json
{
  "meeting_id": "abc123xyz",
  "event_id": "abc123xyz",
  "meet_link": "https://meet.google.com/abc-defg-hij",
  "calendar_link": "https://calendar.google.com/event?eid=...",
  "selected_slot": {
    "start_time": "2026-05-21T10:00:00+05:30",
    "end_time": "2026-05-21T11:00:00+05:30",
    "duration_minutes": 60,
    "confidence_score": 85.0,
    "attendee_count": 3,
    "day_of_week": "Wednesday",
    "time_of_day": "10:00 AM"
  },
  "alternative_slots": [
    {
      "start_time": "2026-05-22T14:00:00+05:30",
      "end_time": "2026-05-22T15:00:00+05:30",
      "duration_minutes": 60,
      "confidence_score": 80.0,
      "attendee_count": 3,
      "day_of_week": "Thursday",
      "time_of_day": "02:00 PM"
    }
  ],
  "total_slots_found": 15,
  "message": "Meeting 'Team Sync Meeting' successfully scheduled at 2026-05-21T10:00:00+05:30 with 85.0% confidence"
}
```

### 3. Get Attendee Availability

**Endpoint:** `GET /calendar/attendee-availability`

Gets detailed availability information for multiple attendees.

**Query Parameters:**
- `attendee_emails`: Comma-separated list of email addresses
- `start_date`: Start of time window (ISO format)
- `end_date`: End of time window (ISO format)
- `timezone`: Timezone for the query (default: UTC)

**Example:**
```
GET /calendar/attendee-availability?attendee_emails=user1@example.com,user2@example.com&start_date=2026-05-20T00:00:00Z&end_date=2026-05-21T23:59:59Z&timezone=Asia/Kolkata
```

**Response:**
```json
{
  "time_window": {
    "start": "2026-05-20T00:00:00+00:00",
    "end": "2026-05-21T23:59:59+00:00",
    "timezone": "Asia/Kolkata"
  },
  "attendees": [
    {
      "email": "user1@example.com",
      "busy_periods": [
        {
          "start": "2026-05-20T09:00:00Z",
          "end": "2026-05-20T10:00:00Z"
        },
        {
          "start": "2026-05-20T14:00:00Z",
          "end": "2026-05-20T15:30:00Z"
        }
      ],
      "has_errors": false,
      "errors": []
    },
    {
      "email": "user2@example.com",
      "busy_periods": [
        {
          "start": "2026-05-20T11:00:00Z",
          "end": "2026-05-20T12:00:00Z"
        }
      ],
      "has_errors": false,
      "errors": []
    }
  ],
  "total_attendees": 2
}
```

## How It Works

### 1. Availability Analysis
The system queries Google Calendar's Free/Busy API for all attendees to get their busy time slots within the specified date range.

### 2. Free Slot Detection
The algorithm:
- Iterates through the time window in 15-minute increments
- Checks if each potential slot conflicts with any attendee's busy periods
- Filters out non-working hours and weekends
- Ensures the full meeting duration fits without conflicts

### 3. Confidence Scoring
Each free slot receives a confidence score (0-100) based on:

**Time of Day Factors:**
- 10-11 AM or 2-3 PM: +20 points (prime meeting times)
- 9-10 AM, 1-2 PM, or 3-4 PM: +10 points (good times)
- Before 9 AM or after 5 PM: -15 points (less desirable)

**Day of Week Factors:**
- Tuesday, Wednesday, Thursday: +10 points (best days)
- Monday (after 10 AM): +5 points
- Monday (before 10 AM): -10 points (avoid Monday mornings)
- Friday (before 3 PM): +5 points
- Friday (after 3 PM): -10 points (avoid Friday afternoons)

**Meeting Characteristics:**
- Duration ≤ 30 minutes: +5 points
- Duration ≥ 120 minutes: -5 points
- Attendee count ≤ 3: +10 points
- Attendee count ≤ 5: +5 points
- Attendee count ≥ 10: -5 points

### 4. Automatic Scheduling
When using the auto-schedule endpoint:
1. System finds all available slots
2. Ranks them by confidence score
3. Selects the highest-scoring slot
4. Creates a Google Calendar event with Google Meet link
5. Sends invitations to all attendees
6. Returns the meeting details with alternative options

## Usage Examples

### Python Example

```python
import requests
from datetime import datetime, timedelta

# API endpoint
base_url = "http://localhost:8000"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Auto-schedule a meeting
response = requests.post(
    f"{base_url}/calendar/auto-schedule",
    headers=headers,
    json={
        "title": "Project Planning Meeting",
        "description": "Discuss Q2 project roadmap",
        "attendee_emails": [
            "alice@company.com",
            "bob@company.com",
            "charlie@company.com"
        ],
        "duration_minutes": 90,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "timezone": "Asia/Kolkata",
        "working_hours_start": 9,
        "working_hours_end": 18,
        "is_online": True
    }
)

result = response.json()
print(f"Meeting scheduled at: {result['selected_slot']['start_time']}")
print(f"Google Meet link: {result['meet_link']}")
print(f"Confidence score: {result['selected_slot']['confidence_score']}%")
```

### JavaScript/TypeScript Example

```typescript
const scheduleTeamMeeting = async () => {
  const response = await fetch('http://localhost:8000/calendar/auto-schedule', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: 'Sprint Planning',
      description: 'Plan next sprint tasks',
      attendee_emails: [
        'dev1@company.com',
        'dev2@company.com',
        'manager@company.com'
      ],
      duration_minutes: 60,
      start_date: new Date().toISOString(),
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      timezone: 'Asia/Kolkata',
      working_hours_start: 9,
      working_hours_end: 17,
      is_online: true
    })
  });

  const result = await response.json();
  console.log('Meeting scheduled:', result.selected_slot.start_time);
  console.log('Meet link:', result.meet_link);
};
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/calendar/auto-schedule" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "description": "Daily standup meeting",
    "attendee_emails": [
      "team1@company.com",
      "team2@company.com"
    ],
    "duration_minutes": 30,
    "start_date": "2026-05-20T00:00:00Z",
    "end_date": "2026-05-27T23:59:59Z",
    "timezone": "Asia/Kolkata",
    "working_hours_start": 9,
    "working_hours_end": 17,
    "is_online": true
  }'
```

## Best Practices

1. **Search Window**: Use a reasonable date range (7-14 days) for better performance
2. **Working Hours**: Set appropriate working hours for your team's timezone
3. **Duration**: Keep meetings under 2 hours for better slot availability
4. **Attendee Count**: Limit to essential attendees for easier scheduling
5. **Timezone**: Always specify the correct timezone for accurate scheduling

## Troubleshooting

### No Available Slots Found
- Expand the search window (more days)
- Reduce meeting duration
- Adjust working hours
- Reduce number of attendees
- Check if attendees have granted calendar access

### Low Confidence Scores
- Slots with scores below 50 are available but not optimal
- Consider alternative times or days
- Review attendee availability patterns

### Calendar Access Issues
- Ensure all attendees have granted calendar access permissions
- Verify OAuth scopes include calendar read access
- Check that attendees' calendars are not private

## Security & Privacy

- Only free/busy information is accessed (not event details)
- Attendees must grant calendar access permissions
- All data is encrypted in transit
- No calendar data is stored permanently
- Complies with Google Calendar API terms of service

## Future Enhancements

- Support for recurring meetings
- Integration with Microsoft Outlook calendars
- Custom scoring algorithms per organization
- Meeting room availability integration
- Time zone optimization for distributed teams
- ML-based preference learning

---

**Made with Bob** 🤖