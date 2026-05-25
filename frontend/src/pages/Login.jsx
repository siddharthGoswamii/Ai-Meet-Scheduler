import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Login() {

  const handleGoogleLogin = async () => {
    try {
      const res = await axios.get(
        `${API_URL}/api/auth/login`,
        { withCredentials: true }
      );
      if (res.data && res.data.authorization_url) {
        window.location.href = res.data.authorization_url;
      } else {
        console.error('Authorization URL missing:', res.data);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to start Google login');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#060912',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      boxSizing: 'border-box',
      position: 'relative',
      overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>

      {/* Glow blobs */}
      <div style={{
        position: 'absolute', top: '-120px', left: '50%',
        transform: 'translateX(-50%)', width: '500px', height: '500px',
        background: 'radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%)',
        pointerEvents: 'none'
      }}/>
      <div style={{
        position: 'absolute', bottom: '-80px', right: '80px',
        width: '300px', height: '300px',
        background: 'radial-gradient(ellipse, rgba(20,184,166,0.08) 0%, transparent 70%)',
        pointerEvents: 'none'
      }}/>

      <div style={{ width: '100%', maxWidth: '420px', position: 'relative', zIndex: 1 }}>

        {/* Main card */}
        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: '0.5px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '48px 40px',
          textAlign: 'center'
        }}>

          {/* Logo + name */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '32px' }}>
            <div style={{
              width: '36px', height: '36px',
              background: 'rgba(99,102,241,0.15)',
              border: '0.5px solid rgba(99,102,241,0.4)',
              borderRadius: '10px',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
                <circle cx="12" cy="16" r="2" fill="#818cf8" stroke="none"/>
              </svg>
            </div>
            <span style={{ fontSize: '15px', fontWeight: '500', color: '#e2e8f0', letterSpacing: '-0.3px' }}>
              AI Meet Scheduler
            </span>
          </div>

          {/* Headline */}
          <h1 style={{ fontSize: '26px', fontWeight: '500', color: '#f1f5f9', margin: '0 0 10px', letterSpacing: '-0.5px', lineHeight: '1.2' }}>
            Schedule smarter,<br/>not harder
          </h1>
          <p style={{ fontSize: '14px', color: '#64748b', lineHeight: '1.6', margin: '0 0 28px' }}>
            AI-powered availability detection and cross-calendar coordination — from a single click.
          </p>

          {/* Stats */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '28px', justifyContent: 'center' }}>
            {[
              { value: '2x', label: 'faster scheduling', color: '#818cf8', bg: 'rgba(99,102,241,0.08)', border: 'rgba(99,102,241,0.2)' },
              { value: 'AI', label: 'slot suggestions',  color: '#2dd4bf', bg: 'rgba(20,184,166,0.08)',  border: 'rgba(20,184,166,0.2)' },
              { value: '0',  label: 'back-and-forth',    color: '#fbbf24', bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.2)' },
            ].map((s, i) => (
              <div key={i} style={{
                background: s.bg, border: `0.5px solid ${s.border}`,
                borderRadius: '8px', padding: '8px 14px', textAlign: 'center', flex: 1
              }}>
                <div style={{ fontSize: '18px', fontWeight: '500', color: s.color }}>{s.value}</div>
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Google button */}
          <button
            onClick={handleGoogleLogin}
            style={{
              width: '100%',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
              background: '#ffffff', color: '#0f172a',
              border: 'none', padding: '14px 20px',
              borderRadius: '12px', fontSize: '15px',
              fontWeight: '500', cursor: 'pointer',
              transition: 'all 0.15s', marginBottom: '16px'
            }}
            onMouseOver={e => { e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
            onMouseOut={e => { e.currentTarget.style.background = '#ffffff'; e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
              <path d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.47h4.84c-.21 1.12-.84 2.07-1.79 2.7v2.24h2.9c1.69-1.55 2.69-3.85 2.69-6.57z" fill="#4285F4"/>
              <path d="M9 18c2.43 0 4.47-.8 5.96-2.23l-2.9-2.24c-.8.54-1.84.87-3.06.87-2.35 0-4.35-1.59-5.06-3.73H.96v2.3C2.44 15.93 5.48 18 9 18z" fill="#34A853"/>
              <path d="M3.94 10.67c-.18-.54-.28-1.11-.28-1.67s.1-1.13.28-1.67V5.03H.96C.35 6.24 0 7.59 0 9s.35 2.76.96 3.97l2.98-2.3z" fill="#FBBC05"/>
              <path d="M9 3.58c1.32 0 2.5.45 3.44 1.35L15 2.1C13.46.66 11.42 0 9 0 5.48 0 2.44 2.07.96 5.03l2.98 2.3c.71-2.14 2.71-3.73 5.06-3.73z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <div style={{ flex: 1, height: '0.5px', background: 'rgba(255,255,255,0.06)' }}/>
            <span style={{ fontSize: '12px', color: '#334155' }}>connects your Google Calendar</span>
            <div style={{ flex: 1, height: '0.5px', background: 'rgba(255,255,255,0.06)' }}/>
          </div>

          {/* Trust badges */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            {[
              { icon: '🔐', text: 'OAuth 2.0' },
              { icon: '🔒', text: 'Encrypted' },
              { icon: '🚫', text: 'No data stored' },
            ].map((b, i) => (
              <span key={i} style={{ fontSize: '12px', color: '#334155' }}>{b.icon} {b.text}</span>
            ))}
          </div>

        </div>

        {/* Feature pills */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '20px', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            background: 'rgba(20,184,166,0.08)', border: '0.5px solid rgba(20,184,166,0.2)',
            borderRadius: '6px', padding: '4px 10px'
          }}>
            <span style={{ fontSize: '12px', color: '#2dd4bf' }}>✦ AI-powered suggestions</span>
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            background: 'rgba(99,102,241,0.08)', border: '0.5px solid rgba(99,102,241,0.2)',
            borderRadius: '6px', padding: '4px 10px'
          }}>
            <span style={{ fontSize: '12px', color: '#818cf8' }}>✦ Google Meet integration</span>
          </div>
        </div>

      </div>
    </div>
  );
}