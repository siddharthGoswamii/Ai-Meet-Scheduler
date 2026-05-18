-- Database setup script for Google Meet Scheduler (gmeet_scheduler)
-- Run this script to create the database and all tables

-- Create database
CREATE DATABASE gmeet_scheduler;

-- Connect to the database
\c gmeet_scheduler;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

-- Meeting status enumeration
CREATE TYPE meeting_status AS ENUM ('scheduled', 'cancelled', 'completed');

-- Attendee response status enumeration
CREATE TYPE response_status AS ENUM ('none', 'accepted', 'declined', 'tentative');

-- Reminder type enumeration
CREATE TYPE reminder_type AS ENUM ('email', 'notification', 'both');

-- ============================================================================
-- TABLES
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    teams_user_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Encrypted tokens
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- User preferences
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_teams_user_id ON users(teams_user_id);

-- Meetings table
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organizer_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    teams_meeting_id VARCHAR(255) UNIQUE,
    
    -- Meeting details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Time information
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    
    -- Location
    location VARCHAR(500),
    is_online BOOLEAN NOT NULL DEFAULT TRUE,
    meeting_url TEXT,
    
    -- Status
    status meeting_status NOT NULL DEFAULT 'scheduled',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_meeting_time CHECK (end_time > start_time)
);

-- Create indexes for meetings table
CREATE INDEX idx_meetings_organizer_id ON meetings(organizer_id);
CREATE INDEX idx_meetings_teams_meeting_id ON meetings(teams_meeting_id);
CREATE INDEX idx_meetings_start_time ON meetings(start_time);
CREATE INDEX idx_meetings_end_time ON meetings(end_time);
CREATE INDEX idx_meetings_status ON meetings(status);

-- Meeting attendees table
CREATE TABLE IF NOT EXISTS meeting_attendees (
    attendee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Attendee information
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    
    -- Response status
    response_status response_status NOT NULL DEFAULT 'none',
    
    -- Attendee properties
    is_organizer BOOLEAN NOT NULL DEFAULT FALSE,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Timestamps
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    response_time TIMESTAMP WITH TIME ZONE
);

-- Create indexes for meeting_attendees table
CREATE INDEX idx_meeting_attendees_meeting_id ON meeting_attendees(meeting_id);
CREATE INDEX idx_meeting_attendees_user_id ON meeting_attendees(user_id);
CREATE INDEX idx_meeting_attendees_email ON meeting_attendees(email);

-- Meeting reminders table
CREATE TABLE IF NOT EXISTS meeting_reminders (
    reminder_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Reminder settings
    reminder_time TIMESTAMP WITH TIME ZONE NOT NULL,
    reminder_type reminder_type NOT NULL DEFAULT 'notification',
    
    -- Status
    is_sent BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for meeting_reminders table
CREATE INDEX idx_meeting_reminders_meeting_id ON meeting_reminders(meeting_id);
CREATE INDEX idx_meeting_reminders_user_id ON meeting_reminders(user_id);
CREATE INDEX idx_meeting_reminders_reminder_time ON meeting_reminders(reminder_time);
CREATE INDEX idx_meeting_reminders_is_sent ON meeting_reminders(is_sent);

-- AI scheduling suggestions table
CREATE TABLE IF NOT EXISTS ai_scheduling_suggestions (
    suggestion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Request information
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(meeting_id) ON DELETE SET NULL,
    
    -- Scheduling parameters
    duration_minutes INTEGER NOT NULL,
    attendee_emails TEXT[] NOT NULL,
    attendee_count INTEGER NOT NULL,
    
    -- Time slot information
    suggested_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    suggested_end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    
    -- AI scoring and analysis
    confidence_score DECIMAL(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    recommendation_text TEXT,
    suggestion_reason TEXT,
    
    -- Availability data
    organizer_availability VARCHAR(50),
    attendee_availability_summary JSONB,
    
    -- Preference matching
    preferred_days TEXT[],
    preferred_hours_start INTEGER,
    preferred_hours_end INTEGER,
    matches_preferences BOOLEAN DEFAULT FALSE,
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'suggested',
    is_accepted BOOLEAN DEFAULT FALSE,
    is_rejected BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    
    -- Search window
    search_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    search_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- API response metadata
    graph_api_confidence DECIMAL(5,2),
    api_response_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_time_range CHECK (suggested_end_time > suggested_start_time),
    CONSTRAINT valid_search_window CHECK (search_end_date > search_start_date),
    CONSTRAINT valid_status CHECK (status IN ('suggested', 'accepted', 'rejected', 'expired'))
);

-- Create indexes for ai_scheduling_suggestions table
CREATE INDEX idx_ai_suggestions_user_id ON ai_scheduling_suggestions(user_id);
CREATE INDEX idx_ai_suggestions_meeting_id ON ai_scheduling_suggestions(meeting_id);
CREATE INDEX idx_ai_suggestions_start_time ON ai_scheduling_suggestions(suggested_start_time);
CREATE INDEX idx_ai_suggestions_confidence ON ai_scheduling_suggestions(confidence_score DESC);
CREATE INDEX idx_ai_suggestions_status ON ai_scheduling_suggestions(status);
CREATE INDEX idx_ai_suggestions_created_at ON ai_scheduling_suggestions(created_at DESC);
CREATE INDEX idx_ai_suggestions_accepted ON ai_scheduling_suggestions(is_accepted) WHERE is_accepted = TRUE;
CREATE INDEX idx_ai_suggestions_user_status ON ai_scheduling_suggestions(user_id, status);
CREATE INDEX idx_ai_suggestions_user_time ON ai_scheduling_suggestions(user_id, suggested_start_time);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Function to automatically update updated_at timestamp for users
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Function to automatically update updated_at timestamp for meetings
CREATE OR REPLACE FUNCTION update_meetings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_meetings_timestamp
    BEFORE UPDATE ON meetings
    FOR EACH ROW
    EXECUTE FUNCTION update_meetings_updated_at();

-- Function to automatically update updated_at timestamp for AI suggestions
CREATE OR REPLACE FUNCTION update_ai_suggestions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ai_suggestions_timestamp
    BEFORE UPDATE ON ai_scheduling_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_suggestions_updated_at();

-- Function to set accepted_at timestamp for AI suggestions
CREATE OR REPLACE FUNCTION set_ai_suggestion_accepted_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_accepted = TRUE AND OLD.is_accepted = FALSE THEN
        NEW.accepted_at = CURRENT_TIMESTAMP;
        NEW.status = 'accepted';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_accepted_timestamp
    BEFORE UPDATE ON ai_scheduling_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION set_ai_suggestion_accepted_at();

-- Function to set rejected_at timestamp for AI suggestions
CREATE OR REPLACE FUNCTION set_ai_suggestion_rejected_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_rejected = TRUE AND OLD.is_rejected = FALSE THEN
        NEW.rejected_at = CURRENT_TIMESTAMP;
        NEW.status = 'rejected';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_rejected_timestamp
    BEFORE UPDATE ON ai_scheduling_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION set_ai_suggestion_rejected_at();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for active AI suggestions
CREATE OR REPLACE VIEW active_ai_suggestions AS
SELECT 
    s.*,
    u.email as user_email,
    u.display_name as user_name,
    m.title as meeting_title
FROM ai_scheduling_suggestions s
JOIN users u ON s.user_id = u.user_id
LEFT JOIN meetings m ON s.meeting_id = m.meeting_id
WHERE s.status = 'suggested'
  AND s.suggested_start_time > CURRENT_TIMESTAMP
ORDER BY s.confidence_score DESC, s.created_at DESC;

-- View for AI suggestion analytics
CREATE OR REPLACE VIEW ai_suggestion_analytics AS
SELECT 
    user_id,
    COUNT(*) as total_suggestions,
    COUNT(*) FILTER (WHERE is_accepted = TRUE) as accepted_count,
    COUNT(*) FILTER (WHERE is_rejected = TRUE) as rejected_count,
    AVG(confidence_score) as avg_confidence_score,
    AVG(confidence_score) FILTER (WHERE is_accepted = TRUE) as avg_accepted_confidence,
    AVG(confidence_score) FILTER (WHERE is_rejected = TRUE) as avg_rejected_confidence,
    MAX(created_at) as last_suggestion_date
FROM ai_scheduling_suggestions
GROUP BY user_id;

-- View for upcoming meetings
CREATE OR REPLACE VIEW upcoming_meetings AS
SELECT 
    m.*,
    u.email as organizer_email,
    u.display_name as organizer_name,
    COUNT(ma.attendee_id) as attendee_count
FROM meetings m
JOIN users u ON m.organizer_id = u.user_id
LEFT JOIN meeting_attendees ma ON m.meeting_id = ma.meeting_id
WHERE m.status = 'scheduled'
  AND m.start_time > CURRENT_TIMESTAMP
GROUP BY m.meeting_id, u.email, u.display_name
ORDER BY m.start_time ASC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Stores user information and authentication tokens';
COMMENT ON TABLE meetings IS 'Stores meeting information and details';
COMMENT ON TABLE meeting_attendees IS 'Stores meeting participant information';
COMMENT ON TABLE meeting_reminders IS 'Stores meeting reminder settings';
COMMENT ON TABLE ai_scheduling_suggestions IS 'Stores AI-generated meeting time suggestions with confidence scores';

COMMENT ON COLUMN ai_scheduling_suggestions.confidence_score IS 'AI confidence score (0-100) for the suggested time slot';
COMMENT ON COLUMN ai_scheduling_suggestions.attendee_availability_summary IS 'JSON summary of attendee availability data';
COMMENT ON COLUMN ai_scheduling_suggestions.api_response_data IS 'Full API response data for debugging and analysis';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

SELECT 'Database gmeet_scheduler setup complete!' as status,
       'All tables, indexes, triggers, and views have been created.' as message;

-- Made with Bob