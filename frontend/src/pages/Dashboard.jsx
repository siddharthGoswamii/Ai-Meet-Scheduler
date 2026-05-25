import { useEffect, useMemo, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Dashboard() {
    const [searchParams] = useSearchParams();
    const navigate      = useNavigate();

    const [date, setDate]               = useState('');
    const [duration, setDuration]       = useState(60);
    const [emails, setEmails]           = useState('');
    const [meetingTitle, setMeetingTitle] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [bookedSlots, setBookedSlots] = useState([]);
    const [loading, setLoading]         = useState(false);
    const [cancellingSlot, setCancellingSlot] = useState('');
    const [meetLink, setMeetLink]       = useState('');
    const [token, setToken]             = useState('');
    
    // Time selection modal state
    const [showTimeModal, setShowTimeModal] = useState(false);
    const [selectedSlot, setSelectedSlot] = useState(null);
    const [customStartTime, setCustomStartTime] = useState('');
    const [customEndTime, setCustomEndTime] = useState('');

    // ── Step 1: Get token from URL on load ──
    useEffect(() => {
        const urlToken = searchParams.get('token');
        if (urlToken) {
            localStorage.setItem('access_token', urlToken);
            setToken(urlToken);
            navigate('/dashboard', { replace: true });
        } else {
            const saved = localStorage.getItem('access_token');
            if (saved) {
                setToken(saved);
            } else {
                navigate('/');
            }
        }
    }, [searchParams, navigate]);

    // ── Step 2: Get auth headers ──
    const getHeaders = useCallback(() => ({
        headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
    }), []);

    const formatSlotTime = (isoString) => {
        const slotDate = new Date(isoString);
        return slotDate.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    };

    const fetchBookedSlots = useCallback(async (selectedDate = date) => {
        if (!selectedDate) return;

        try {
            const res = await axios.get(
                `${API_URL}/api/meetings`,
                {
                    ...getHeaders(),
                    params: {
                        start_date: `${selectedDate}T00:00:00`,
                        end_date: `${selectedDate}T23:59:59`,
                        page: 1,
                        page_size: 100
                    }
                }
            );

            const meetings = res?.data?.meetings || [];
            const scheduledMeetings = meetings.filter(
                meeting => String(meeting.status).toLowerCase() === 'scheduled'
            );

            setBookedSlots(
                scheduledMeetings.map(meeting => ({
                    meeting_id: meeting.meeting_id,
                    meeting_url: meeting.meeting_url || '',
                    start: formatSlotTime(meeting.start_time),
                    end: formatSlotTime(meeting.end_time),
                    reason: meeting.title || 'Meeting booked successfully'
                }))
            );
        } catch (err) {
            console.error('Failed to fetch booked slots:', err?.response?.data || err);
        }
    }, [date, getHeaders]);

    // ── Step 3: Get AI suggestions ──
    const getSuggestions = async () => {
        if (!date || !emails) {
            alert('Please select a target date and provide participant emails.');
            return;
        }

        setLoading(true);
        setSuggestions([]);

        try {
            const res = await axios.post(
                `${API_URL}/api/meetings/suggest`,
                {
                    participants:     emails.split(',').map(e => e.trim()),
                    duration_mins:    parseInt(duration),
                    preferred_date:   date  // Add the date field!
                },
                getHeaders()
            );
            const nextSuggestions = res.data.suggestions || [];
            setSuggestions(nextSuggestions);
            await fetchBookedSlots(date);
        } catch (err) {
            console.error(err);
            alert('Failed to fetch AI suggestions. Is your backend running?');
        } finally {
            setLoading(false);
        }
    };

    // ── Step 4: Open time selection modal ──
    const openTimeSelectionModal = (slot) => {
        // Prompt for meeting title if not provided
        if (!meetingTitle || meetingTitle.trim() === '') {
            alert('Please enter a meeting title before booking a slot.');
            return;
        }
        
        setSelectedSlot(slot);
        setCustomStartTime(slot.start);
        
        // Calculate end time based on selected duration
        const startMinutes = timeToMinutes(slot.start);
        const endMinutes = startMinutes + parseInt(duration);
        const endHours = Math.floor(endMinutes / 60);
        const endMins = endMinutes % 60;
        const calculatedEndTime = `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`;
        
        // Make sure calculated end time doesn't exceed slot end time
        const slotEndMinutes = timeToMinutes(slot.end);
        if (endMinutes <= slotEndMinutes) {
            setCustomEndTime(calculatedEndTime);
        } else {
            setCustomEndTime(slot.end);
        }
        
        setShowTimeModal(true);
    };

    // Handle start time change and auto-adjust end time
    const handleStartTimeChange = (newStartTime) => {
        setCustomStartTime(newStartTime);
        
        // Auto-calculate end time based on duration
        const startMinutes = timeToMinutes(newStartTime);
        const endMinutes = startMinutes + parseInt(duration);
        const endHours = Math.floor(endMinutes / 60);
        const endMins = endMinutes % 60;
        const calculatedEndTime = `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`;
        
        // Make sure calculated end time doesn't exceed slot end time
        if (selectedSlot) {
            const slotEndMinutes = timeToMinutes(selectedSlot.end);
            if (endMinutes <= slotEndMinutes) {
                setCustomEndTime(calculatedEndTime);
            } else {
                setCustomEndTime(selectedSlot.end);
            }
        }
    };

    // Helper function to convert time string (HH:MM) to minutes
    const timeToMinutes = (timeStr) => {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    };

    // ── Step 5: Book a meeting with custom time ──
    const bookMeeting = async () => {
        if (!selectedSlot) return;

        // Validate custom time range
        const slotStartMinutes = timeToMinutes(selectedSlot.start);
        const slotEndMinutes = timeToMinutes(selectedSlot.end);
        const customStartMinutes = timeToMinutes(customStartTime);
        const customEndMinutes = timeToMinutes(customEndTime);

        if (customStartMinutes < slotStartMinutes || customEndMinutes > slotEndMinutes) {
            alert(`Please select a time range within the available slot (${selectedSlot.start} - ${selectedSlot.end})`);
            return;
        }

        if (customStartMinutes >= customEndMinutes) {
            alert('End time must be after start time.');
            return;
        }

        // Validate that the selected duration matches the requested duration
        const selectedDuration = customEndMinutes - customStartMinutes;
        if (selectedDuration !== parseInt(duration)) {
            alert(`Please select exactly ${duration} minutes duration. Currently selected: ${selectedDuration} minutes.`);
            return;
        }

        let createdEvent = null;

        try {
            // Parse the date and times correctly
            const startDateTime = new Date(`${date}T${customStartTime}:00`);
            const endDateTime = new Date(`${date}T${customEndTime}:00`);

            createdEvent = await axios.post(
                `${API_URL}/api/meetings`,
                {
                    title: meetingTitle.trim(),
                    description: 'Scheduled via AI Meeting Scheduler',
                    start_time: startDateTime.toISOString(),
                    end_time: endDateTime.toISOString(),
                    timezone: 'Asia/Kolkata',
                    attendees: emails.split(',').map(e => ({
                        email: e.trim(),
                        display_name: e.trim().split('@')[0],
                        is_required: true
                    })),
                    is_online: true,
                    send_invitations: true
                },
                getHeaders()
            );

            const link = createdEvent?.data?.meeting_url || '';
            const meetingId = createdEvent?.data?.meeting_id || '';
            setMeetLink(link);
            
            // Add booked slot with custom times
            const bookedSlot = {
                start: customStartTime,
                end: customEndTime,
                meeting_url: link,
                meeting_id: meetingId,
                reason: meetingTitle
            };
            setBookedSlots(prev => [...prev, bookedSlot]);
            
            // Remove the original suggestion slot
            setSuggestions(prev => prev.filter(s => !(s.start === selectedSlot.start && s.end === selectedSlot.end)));
            
            // Close modal and reset
            setShowTimeModal(false);
            setSelectedSlot(null);
            
            alert(`✅ Meeting booked successfully!\nTime: ${customStartTime} - ${customEndTime}\nLink: ${link}`);

        } catch (err) {
            const status = err?.response?.status;
            const responseData = err?.response?.data;
            console.error('Booking error:', responseData || err);

            const fallbackLink =
                createdEvent?.data?.meeting_url ||
                responseData?.meeting_url ||
                responseData?.meet_link ||
                '';

            const likelyCreated =
                !!fallbackLink ||
                (typeof responseData?.detail === 'string' &&
                    /already created|already booked|response validation|serialization/i.test(responseData.detail));

            if (likelyCreated) {
                setMeetLink(fallbackLink);
                const bookedSlot = {
                    start: customStartTime,
                    end: customEndTime,
                    meeting_url: fallbackLink,
                    reason: meetingTitle
                };
                setBookedSlots(prev => [...prev, bookedSlot]);
                setSuggestions(prev => prev.filter(s => !(s.start === selectedSlot.start && s.end === selectedSlot.end)));
                setShowTimeModal(false);
                setSelectedSlot(null);
                alert(`✅ Meeting booked successfully!\nTime: ${customStartTime} - ${customEndTime}${fallbackLink ? `\nLink: ${fallbackLink}` : ''}`);
                return;
            }

            alert(
                `Failed to book the selected slot${status ? ` (${status})` : ''}. ` +
                `${responseData?.detail || 'Check console for details.'}`
            );
        }
    };

    const cancelBookedSlot = async (slot) => {
        if (!slot.meeting_id) {
            alert('This booked slot cannot be cancelled from dashboard because the meeting ID is unavailable.');
            return;
        }

        const confirmed = window.confirm(`Cancel booked slot ${slot.start} — ${slot.end}?`);
        if (!confirmed) return;

        try {
            setCancellingSlot(slot.meeting_id);

            await axios.delete(
                `${API_URL}/api/meetings/${slot.meeting_id}`,
                {
                    ...getHeaders(),
                    data: {
                        cancellation_message: 'Cancelled from dashboard',
                        send_cancellation: true
                    }
                }
            );

            setBookedSlots(prev => prev.filter(s => s.meeting_id !== slot.meeting_id));
            setSuggestions(prev => [...prev, {
                start: slot.start,
                end: slot.end,
                reason: slot.reason
            }]);

            if (meetLink === slot.meeting_url) {
                setMeetLink('');
            }

            alert('✅ Slot cancelled successfully.');
        } catch (err) {
            console.error('Cancel meeting error:', err?.response?.data || err);
            alert(`Failed to cancel slot. ${err?.response?.data?.detail || 'Check console for details.'}`);
        } finally {
            setCancellingSlot('');
        }
    };

    useEffect(() => {
        if (!token || !date) return;
        fetchBookedSlots(date);
    }, [token, date, fetchBookedSlots]);

    const visibleSuggestions = useMemo(
        () => suggestions.filter(
            suggestion => !bookedSlots.some(
                bookedSlot => bookedSlot.start === suggestion.start && bookedSlot.end === suggestion.end
            )
        ),
        [suggestions, bookedSlots]
    );

    // ── Step 5: Logout with Confirmation ──
    const logout = () => {
        const confirmed = window.confirm('Are you sure you want to log out?');
        if (confirmed) {
            localStorage.removeItem('access_token');
            navigate('/');
        }
    };

    // Hackathon Cyber-Dark Theme Styles
    const styles = {
        container: {
            padding: '60px 24px',
            background: 'linear-gradient(180deg, #0b0f19 0%, #05070c 100%)',
            minHeight: '100vh',
            color: '#f3f4f6',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
        },
        wrapper: {
            width: '100%',
            maxWidth: '640px'
        },
        header: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '48px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            paddingBottom: '24px'
        },
        titleContainer: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        badge: {
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: '#60a5fa',
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontWeight: '700'
        },
        title: {
            fontSize: '22px',
            fontWeight: '800',
            letterSpacing: '-0.5px',
            margin: 0,
            color: '#ffffff'
        },
        logoutBtn: {
            background: 'transparent',
            color: '#9ca3af',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500',
            fontSize: '13px',
            transition: 'all 0.2s ease-in-out'
        },
        card: {
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            padding: '36px',
            borderRadius: '16px',
            marginBottom: '32px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)'
        },
        sectionHeading: {
            marginTop: 0,
            marginBottom: '28px',
            fontSize: '18px',
            fontWeight: '600',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        },
        label: {
            display: 'block',
            fontSize: '12px',
            fontWeight: '600',
            color: '#9ca3af',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px'
        },
        fieldGroup: {
            flex: 1,
            display: 'flex',
            flexDirection: 'column'
        },
        row: {
            display: 'flex',
            gap: '16px',
            marginBottom: '24px'
        },
        input: {
            width: '100%',
            padding: '12px 16px',
            borderRadius: '10px',
            background: '#1f2937',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            fontSize: '15px',
            outline: 'none',
            transition: 'all 0.2s ease',
            boxSizing: 'border-box'
        },
        primaryBtn: {
            width: '100%',
            background: '#3b82f6',
            color: '#ffffff',
            padding: '14px 28px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '15px',
            letterSpacing: '0.2px',
            transition: 'all 0.2s ease'
        },
        slotCard: {
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '14px',
            padding: '24px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '20px',
            transition: 'all 0.2s ease'
        },
        slotInfo: {
            flex: 1
        },
        slotTitle: {
            color: '#ffffff',
            margin: '0 0 6px 0',
            fontSize: '16px',
            fontWeight: '600'
        },
        slotReason: {
            color: '#9ca3af',
            margin: 0,
            fontSize: '13px',
            lineHeight: '1.5'
        },
        bookBtn: {
            background: 'transparent',
            color: '#10b981',
            border: '1px solid #10b981',
            padding: '10px 18px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '13px',
            whiteSpace: 'nowrap',
            transition: 'all 0.2s ease'
        },
        successAlert: {
            background: 'rgba(16, 185, 129, 0.04)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '14px',
            padding: '24px',
            marginTop: '24px',
            textAlign: 'center',
            boxShadow: '0 0 20px rgba(16, 185, 129, 0.1)'
        },
        successTitle: {
            color: '#10b981',
            margin: '0 0 12px 0',
            fontSize: '15px',
            fontWeight: '600'
        },
        meetLink: {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#10b981',
            color: '#ffffff',
            textDecoration: 'none',
            fontWeight: '600',
            fontSize: '14px',
            padding: '10px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)',
            transition: 'all 0.2s ease',
            border: 'none',
            cursor: 'pointer'
        },
        slotActions: {
            display: 'flex',
            gap: '12px',
            alignItems: 'center',
            flexWrap: 'wrap',
            justifyContent: 'flex-end'
        },
        cancelBtn: {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'transparent',
            color: '#ef4444',
            border: '1px solid #ef4444',
            fontWeight: '600',
            fontSize: '14px',
            padding: '10px 20px',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
        },
        modalOverlay: {
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
        },
        modalContent: {
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '500px',
            width: '100%',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        },
        modalTitle: {
            color: '#ffffff',
            fontSize: '20px',
            fontWeight: '700',
            marginTop: 0,
            marginBottom: '24px'
        },
        modalLabel: {
            display: 'block',
            fontSize: '12px',
            fontWeight: '600',
            color: '#9ca3af',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px',
            marginTop: '16px'
        },
        timeInput: {
            width: '100%',
            padding: '12px 16px',
            borderRadius: '10px',
            background: '#1f2937',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            fontSize: '15px',
            outline: 'none',
            transition: 'all 0.2s ease',
            boxSizing: 'border-box'
        },
        modalButtons: {
            display: 'flex',
            gap: '12px',
            marginTop: '28px'
        },
        modalBtnPrimary: {
            flex: 1,
            background: '#3b82f6',
            color: '#ffffff',
            padding: '12px 24px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s ease'
        },
        modalBtnSecondary: {
            flex: 1,
            background: 'transparent',
            color: '#9ca3af',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '12px 24px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s ease'
        },
        infoText: {
            color: '#9ca3af',
            fontSize: '13px',
            marginTop: '12px',
            marginBottom: '8px'
        }
    };

    return (
        <div style={styles.container}>
            {/* Embedded styles to give premium interactive micro-animations for judges */}
            <style>{`
                input:focus, select:focus {
                    border-color: #3b82f6 !important;
                    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
                }
                .btn-primary:hover {
                    background: #2563eb !important;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                }
                .btn-logout:hover {
                    color: #ef4444 !important;
                    border-color: #ef4444 !important;
                    background: rgba(239, 68, 68, 0.05);
                }
                .slot-item:hover {
                    border-color: rgba(59, 130, 246, 0.3) !important;
                    background: #141c2f !important;
                }
                .btn-book:hover {
                    background: #10b981 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
                }
                .btn-meet:hover {
                    background: #059669 !important;
                    transform: translateY(-1px);
                }
                .btn-cancel:hover {
                    background: #ef4444 !important;
                    color: #ffffff !important;
                    transform: translateY(-1px);
                }
                .btn-modal-confirm:hover {
                    background: #2563eb !important;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                }
                .btn-modal-cancel:hover {
                    background: rgba(255, 255, 255, 0.05) !important;
                    border-color: rgba(255, 255, 255, 0.2) !important;
                }
            `}</style>

            <div style={styles.wrapper}>

                {/* Header */}
                {/* <div style={styles.header}>
                    <div style={styles.titleContainer}>
                        <h2 style={styles.title}>AI Meet Scheduler</h2>
                        <span style={styles.badge}>v1.0-Beta</span>
                    </div>
                    <button onClick={logout} style={styles.logoutBtn} className="btn-logout">
                        Log Out
                    </button>
                </div> */}
                <div style={styles.header}>
                    <div style={styles.titleContainer}>
                        
                        {/* LEFT SIDE (Title + Quote) */}
                        <div>
                            <div class="feature-icon">🤖</div>
                            <h2 style={styles.title}>AI meet Scheduler</h2>
                            
                            <p style={{
                                margin: '4px 0 0 0',
                                fontSize: '13px',
                                color: '#9ca3af',
                                fontStyle: 'italic'
                            }}>
                                "Smart meetings. Zero conflicts. Maximum productivity."
                            </p>
                        </div>

                        {/* RIGHT SIDE (Badge) */}
                        <span style={styles.badge}>v1.0-Beta</span>

                    </div>

                    <button 
                        onClick={logout} 
                        style={styles.logoutBtn} 
                        className="btn-logout"
                    >
                        Log Out
                    </button>
                </div>

                {/* Main Scheduler Form */}
                <div style={styles.card}>
                    <h3 style={styles.sectionHeading}>
                        <span>📅</span> Create Smart Session
                    </h3>

                    {/* Date & Duration inputs */}
                    <div style={styles.row}>
                        <div style={styles.fieldGroup}>
                            <label style={styles.label}>Target Date</label>
                            <input
                                type="date"
                                value={date}
                                onChange={e => setDate(e.target.value)}
                                min={new Date().toISOString().split('T')[0]}
                                style={styles.input}
                                onKeyDown={(e) => e.preventDefault()}
                            />
                        </div>

                        <div style={styles.fieldGroup}>
                            <label style={styles.label}>Duration</label>
                            <select
                                value={duration}
                                onChange={e => setDuration(e.target.value)}
                                style={{ ...styles.input, cursor: 'pointer' }}
                            >
                                <option value={30}>30 mins</option>
                                <option value={60}>1 hour</option>
                                <option value={90}>1.5 hours</option>
                            </select>
                        </div>
                    </div>

                    {/* Meeting Title input */}
                    <div style={{ ...styles.fieldGroup, marginBottom: '24px' }}>
                        <label style={styles.label}>Meeting Title</label>
                        <input
                            type="text"
                            placeholder="e.g. Team Standup, Project Review, Client Meeting"
                            value={meetingTitle}
                            onChange={e => setMeetingTitle(e.target.value)}
                            style={styles.input}
                        />
                    </div>

                    {/* Emails inputs */}
                    <div style={{ ...styles.fieldGroup, marginBottom: '28px' }}>
                        <label style={styles.label}>Required Attendees</label>
                        <input
                            placeholder="e.g. dev@hack.com, designer@hack.com"
                            value={emails}
                            onChange={e => setEmails(e.target.value)}
                            style={styles.input}
                        />
                    </div>

                    {/* Action Button */}
                    <button
                        onClick={getSuggestions}
                        disabled={loading}
                        className="btn-primary"
                        style={{
                            ...styles.primaryBtn,
                            background: loading ? '#374151' : '#3b82f6',
                            color: loading ? '#9ca3af' : '#ffffff',
                            cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {loading ? 'Analyzing Calendars...' : 'Find Optimal Meeting Slots'}
                    </button>
                </div>

                {/* AI Generated Suggestions Panel */}
                {visibleSuggestions.length > 0 && (
                    <div style={{ marginBottom: '32px' }}>
                        <h3 style={styles.sectionHeading}>
                            <span>🎯</span> Recommended Slots
                        </h3>
                        {visibleSuggestions.map((s, i) => (
                            <div key={i} style={styles.slotCard} className="slot-item">
                                <div style={styles.slotInfo}>
                                    <h4 style={styles.slotTitle}>
                                        {s.start} — {s.end}
                                    </h4>
                                    <p style={styles.slotReason}>
                                        {s.reason}
                                    </p>
                                </div>
                                <button
                                    onClick={() => openTimeSelectionModal(s)}
                                    className="btn-book"
                                    style={styles.bookBtn}
                                >
                                    Confirm Slot
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Booked Slots Panel */}
                {bookedSlots.length > 0 && (
                    <div style={{ marginBottom: '32px' }}>
                        <h3 style={styles.sectionHeading}>
                            <span>✅</span> Booked Slots
                        </h3>
                        {bookedSlots.map((slot, i) => (
                            <div key={`${slot.start}-${slot.end}-${i}`} style={styles.slotCard}>
                                <div style={styles.slotInfo}>
                                    <h4 style={styles.slotTitle}>
                                        {slot.start} — {slot.end}
                                    </h4>
                                    <p style={styles.slotReason}>
                                        {slot.reason || 'Meeting booked successfully'}
                                    </p>
                                </div>
                                <div style={styles.slotActions}>
                                    {slot.meeting_url && (
                                        <a
                                            href={slot.meeting_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="btn-meet"
                                            style={styles.meetLink}
                                        >
                                            Open Meet
                                        </a>
                                    )}
                                    <button
                                        onClick={() => cancelBookedSlot(slot)}
                                        className="btn-cancel"
                                        style={{
                                            ...styles.cancelBtn,
                                            opacity: cancellingSlot === slot.meeting_id ? 0.7 : 1,
                                            cursor: cancellingSlot === slot.meeting_id ? 'not-allowed' : 'pointer'
                                        }}
                                        disabled={cancellingSlot === slot.meeting_id}
                                    >
                                        {cancellingSlot === slot.meeting_id ? 'Cancelling...' : 'Cancel Slot'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Success Alert Banner */}
                {meetLink && (
                    <div style={styles.successAlert}>
                        <h3 style={styles.successTitle}>
                            🎉 Room Provisioned Successfully
                        </h3>
                        <a
                            href={meetLink}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-meet"
                            style={styles.meetLink}
                        >
                            Launch Google Meet
                        </a>
                    </div>
                )}

                {/* Time Selection Modal */}
                {showTimeModal && selectedSlot && (
                    <div style={styles.modalOverlay} onClick={() => setShowTimeModal(false)}>
                        <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                            <h3 style={styles.modalTitle}>
                                ⏰ Select Meeting Time
                            </h3>
                            
                            <p style={styles.infoText}>
                                Available slot: {selectedSlot.start} — {selectedSlot.end}
                            </p>
                            
                            <p style={{...styles.infoText, color: '#60a5fa', fontWeight: '600'}}>
                                Required duration: {duration} minutes ({duration >= 60 ? `${Math.floor(duration / 60)} hour${Math.floor(duration / 60) > 1 ? 's' : ''}${duration % 60 > 0 ? ` ${duration % 60} min` : ''}` : `${duration} minutes`})
                            </p>
                            
                            <div>
                                <label style={styles.modalLabel}>Start Time</label>
                                <input
                                    type="time"
                                    value={customStartTime}
                                    onChange={(e) => handleStartTimeChange(e.target.value)}
                                    min={selectedSlot.start}
                                    max={selectedSlot.end}
                                    style={styles.timeInput}
                                />
                            </div>
                            
                            <div>
                                <label style={styles.modalLabel}>End Time (Auto-calculated)</label>
                                <input
                                    type="time"
                                    value={customEndTime}
                                    readOnly
                                    style={{...styles.timeInput, backgroundColor: '#0f172a', cursor: 'not-allowed', opacity: 0.7}}
                                />
                            </div>
                            
                            <p style={styles.infoText}>
                                Selected duration: {(() => {
                                    const start = timeToMinutes(customStartTime);
                                    const end = timeToMinutes(customEndTime);
                                    const calcDuration = end - start;
                                    if (calcDuration <= 0) return '0 minutes';
                                    const hours = Math.floor(calcDuration / 60);
                                    const mins = calcDuration % 60;
                                    const durationText = hours > 0
                                        ? `${hours} hour${hours > 1 ? 's' : ''} ${mins > 0 ? `${mins} min` : ''}`
                                        : `${mins} minutes`;
                                    const isCorrect = calcDuration === parseInt(duration);
                                    return (
                                        <span style={{color: isCorrect ? '#10b981' : '#ef4444'}}>
                                            {durationText} {isCorrect ? '✓' : '✗ (must match required duration)'}
                                        </span>
                                    );
                                })()}
                            </p>
                            
                            <div style={styles.modalButtons}>
                                <button
                                    onClick={() => setShowTimeModal(false)}
                                    style={styles.modalBtnSecondary}
                                    className="btn-modal-cancel"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={bookMeeting}
                                    style={styles.modalBtnPrimary}
                                    className="btn-modal-confirm"
                                >
                                    Book Meeting
                                </button>
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}