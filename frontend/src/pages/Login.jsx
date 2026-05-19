// src/pages/Login.jsx

import axios from 'axios';

export default function Login() {

    const handleGoogleLogin = async () => {
        const res = await axios.get('http://localhost:8000/auth/login');
        // Redirect to Google login
        window.location.href = res.data.auth_url;
    };

 return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#0D0D0D'
    }}>
      <h1 style={{ color: '#fff', fontSize: 32 }}>
        🤖 AI Meet Scheduler
      </h1>
      <p style={{ color: '#888', marginBottom: 32 }}>
        Smart meeting scheduling powered by AI
      </p>
      <button
        onClick={() => window.location.href =
          'http://localhost:8000/auth/login'}
        style={{
          background: '#fff',
          color: '#000',
          padding: '12px 28px',
          borderRadius: 8,
          border: 'none',
          cursor: 'pointer',
          fontSize: 16,
          fontWeight: 600
        }}>
        🔵 Login with Google
      </button>
    </div>
  );
}