import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Dashboard() {
    const [searchParams] = useSearchParams();
    const navigate      = useNavigate();

    const [date, setDate]               = useState('');
    const [duration, setDuration]       = useState(60);
    const [emails, setEmails]           = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading]         = useState(false);
    const [meetLink, setMeetLink]       = useState('');
    const [token, setToken]             = useState('');

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
    const getHeaders = () => ({
        headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
    });

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
                'http://127.0.0.1:8000/api/meetings/suggest',
                {
                    attendees:      emails.split(',').map(e => e.trim()),
                    duration_minutes: parseInt(duration),
                    days_ahead:       14
                },
                getHeaders()
            );
            setSuggestions(res.data.suggestions || []);
        } catch (err) {
            console.error(err);
            alert('Failed to fetch AI suggestions. Is your backend running?');
        } finally {
            setLoading(false);
        }
    };

    // ── Step 4: Book a meeting ──
    const bookMeeting = async (slot) => {
        try {
            const res = await axios.post(
                'http://127.0.0.1:8000/api/meetings/create',
                {
                    title:        'Team Meeting',
                    date:          date,
                    start_time:    slot.start,
                    end_time:      slot.end,
                    participants:  emails.split(',').map(e => e.trim()),
                    duration_mins: parseInt(duration)
                },
                getHeaders()
            );

            const link = res.data.meet_link || '';
            setMeetLink(link);
            alert(`✅ Meeting booked successfully!\nLink: ${link}`);

        } catch (err) {
            console.error(err);
            alert('Failed to book the selected slot.');
        }
    };

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
            background: '#10b981',
            color: '#ffffff',
            textDecoration: 'none',
            fontWeight: '600',
            fontSize: '14px',
            padding: '10px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)',
            transition: 'all 0.2s ease'
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
            `}</style>

            <div style={styles.wrapper}>

                {/* Header */}
                <div style={styles.header}>
                    <div style={styles.titleContainer}>
                        <h2 style={styles.title}>AI Scheduler</h2>
                        <span style={styles.badge}>v1.0-Beta</span>
                    </div>
                    <button onClick={logout} style={styles.logoutBtn} className="btn-logout">
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
                                style={styles.input}
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
                {suggestions.length > 0 && (
                    <div style={{ marginBottom: '32px' }}>
                        <h3 style={styles.sectionHeading}>
                            <span>🎯</span> Recommended Slots
                        </h3>
                        {suggestions.map((s, i) => (
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
                                    onClick={() => bookMeeting(s)}
                                    className="btn-book"
                                    style={styles.bookBtn}
                                >
                                    Confirm Slot
                                </button>
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

            </div>
        </div>
    );
}