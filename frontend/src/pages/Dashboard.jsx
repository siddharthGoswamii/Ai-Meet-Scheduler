// src/pages/Dashboard.jsx

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Dashboard() {
    const [date, setDate]               = useState('');
    const [duration, setDuration]       = useState(60);
    const [emails, setEmails]           = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading]         = useState(false);

    useEffect(() => {
        // 1. Read the parameters right out of window.location
        const queryParams = new URLSearchParams(window.location.search);
        const token = queryParams.get('token');
        const refreshToken = queryParams.get('refresh_token');

        if (token && refreshToken) {
            // 2. Save them to local storage for Axios request authorization headers
            localStorage.setItem('token', token);
            localStorage.setItem('refresh_token', refreshToken);
            
            // 3. Clean up the URL bar so it looks nice and doesn't expose raw tokens
            window.history.replaceState({}, document.title, "/dashboard");
        }
    }, []);

    const getSuggestions = async () => {
        setLoading(true);
        try {
            // Pull the token out of local storage
            const token = localStorage.getItem('token');

            const res = await axios.post(
                'http://localhost:8000/ai/suggest-slots',
                {
                    participants:   emails.split(','),
                    duration_mins:  duration,
                    preferred_date: date
                },
                {
                    // FIXED: Added headers configuration block so FastAPI allows the request
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            setSuggestions(res.data.ai_suggestions || []);
        } catch (error) {
            console.error("Error getting suggestions:", error);
            alert("❌ Failed to get suggestions. Make sure you are logged in.");
        } finally {
            setLoading(false);
        }
    };

    const bookMeeting = async (slot) => {
        try {
            // Pull the token out of local storage
            const token = localStorage.getItem('token');

            await axios.post(
                'http://localhost:8000/calendar/create-meeting',
                {
                    title:        'Team Meeting',
                    start_time:   `${date}T${slot.start}:00`,
                    end_time:     `${date}T${slot.end}:00`,
                    participants: emails.split(',')
                },
                {
                    // FIXED: Added headers configuration block here as well
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            alert('✅ Meeting booked! Google Meet link sent!');
        } catch (error) {
            console.error("Error booking meeting:", error);
            alert("❌ Failed to book meeting.");
        }
    };

    return (
        <div style={{padding:32, background:'#0D0D0D', minHeight:'100vh', color:'#fff'}}>

            <h2>🤖 Schedule a Meeting</h2>

            {/* Date picker */}
            <input
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                style={{padding:10, borderRadius:8,
                        background:'#1A1A1A', color:'#fff',
                        border:'1px solid #333', marginBottom:12}}/>

            {/* Duration */}
            <select
                value={duration}
                onChange={e => setDuration(Number(e.target.value))}
                style={{padding:10, borderRadius:8,
                        background:'#1A1A1A', color:'#fff',
                        border:'1px solid #333', marginLeft:12}}>
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
                <option value={90}>1.5 hours</option>
            </select>

            {/* Participants */}
            <input
                placeholder="participant emails (comma separated)"
                value={emails}
                onChange={e => setEmails(e.target.value)}
                style={{display:'block', width:'100%', padding:10,
                        borderRadius:8, background:'#1A1A1A',
                        color:'#fff', border:'1px solid #333',
                        marginTop:12, marginBottom:20}}/>

            {/* Get AI suggestions */}
            <button
                onClick={getSuggestions}
                disabled={!date || !emails}
                style={{background: (!date || !emails) ? '#555' : '#2196F3', color:'#fff',
                        padding:'12px 24px', borderRadius:8,
                        border:'none', cursor: (!date || !emails) ? 'not-allowed' : 'pointer',
                        fontWeight:600}}>
                {loading ? '🤖 AI thinking...' : '✨ Get AI Suggestions'}
            </button>

            {/* Show suggestions */}
            {suggestions.map((s, i) => (
                <div key={i} style={{
                    background:'#1A1A1A', borderRadius:12,
                    padding:20, marginTop:16,
                    border:'1px solid #333'}}>
                    <h3 style={{color:'#2196F3'}}>
                        Option {i+1}: {s.slot}
                    </h3>
                    <p style={{color:'#888'}}>{s.reason}</p>
                    <button
                        onClick={() => bookMeeting(s)}
                        style={{background:'#4CAF50', color:'#fff',
                                padding:'8px 20px', borderRadius:8,
                                border:'none', cursor:'pointer'}}>
                        📅 Book This Slot
                    </button>
                </div>
            ))}
        </div>
    );
}