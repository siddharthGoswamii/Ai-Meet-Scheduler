// import axios from 'axios';

// export default function Login() {

//   // const handleGoogleLogin = async () => {
//   //   try {

//   //     const res = await axios.get(
//   //       'http://127.0.0.1:8000/api/auth/login'
//   //     );

//   //     window.location.href = res.data.authorization_url;

//   //   } catch (error) {
//   //     console.error('Login error:', error);
//   //     alert('Failed to start Google login');
//   //   }
//   // };
//   const handleGoogleLogin = async () => {
//     try {
//       // Add withCredentials: true to allow the session cookie to be saved
//       // const res = await axios.get(
//       //   'http://127.0.0.1:8000/api/auth/login',
//       //   { withCredentials: true } 
//       // );
//       const res = await axios.get(
//   'http://localhost:8000/api/auth/login', // Change 127.0.0.1 to localhost
//   { withCredentials: true }
// );

//       if (res.data && res.data.authorization_url) {
//         window.location.href = res.data.authorization_url;
//       } else {
//         console.error('Authorization URL missing in response:', res.data);
//       }

//     } catch (error) {
//       console.error('Login error:', error);
//       alert('Failed to start Google login');
//     }
//   };

//   return (
//     <div
//       style={{
//         display: 'flex',
//         flexDirection: 'column',
//         justifyContent: 'center',
//         alignItems: 'center',
//         height: '100vh',
//         backgroundColor: 'lightblue'
//       }}
//     >
//       <h1 style={{ color: 'black' }}>
//         AI Meet Scheduler
//       </h1>

//       <p style={{ color: 'black' }}>
//         Smart Meeting Scheduling Powered By AI
//       </p>

//       <button
//         onClick={handleGoogleLogin}
//         style={{
//           padding: '10px 20px',
//           fontSize: '18px',
//           cursor: 'pointer'
//         }}
//       >
//         Login with Google
//       </button>
//     </div>
//   );
// }





import axios from 'axios';

export default function Login() {

  const handleGoogleLogin = async () => {
    try {
      const res = await axios.get(
        'http://localhost:8000/api/auth/login',
        { withCredentials: true }
      );

      if (res.data && res.data.authorization_url) {
        window.location.href = res.data.authorization_url;
      } else {
        console.error('Authorization URL missing in response:', res.data);
      }

    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to start Google login');
    }
  };

  // Professional Enterprise Dark Theme
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(180deg, #0b0f19 0%, #05070c 100%)',
      color: '#f3f4f6',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      padding: '24px',
      boxSizing: 'border-box'
    },
    card: {
      background: '#111827',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      padding: '54px 44px',
      borderRadius: '20px',
      textAlign: 'center',
      maxWidth: '420px',
      width: '100%',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    },
    logoContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
      width: '48px',
      height: '48px',
      borderRadius: '12px',
      marginBottom: '28px',
      boxShadow: '0 8px 16px rgba(59, 130, 246, 0.2)'
    },
    title: {
      fontSize: '26px',
      fontWeight: '800',
      letterSpacing: '-0.5px',
      margin: '0 0 12px 0',
      color: '#ffffff'
    },
    subtitle: {
      color: '#9ca3af',
      fontSize: '15px',
      lineHeight: '1.5',
      margin: '0 0 36px 0',
      maxWidth: '320px'
    },
    googleBtn: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      width: '100%',
      background: '#ffffff',
      color: '#1f2937',
      border: 'none',
      padding: '14px 24px',
      borderRadius: '10px',
      fontSize: '15px',
      fontWeight: '600',
      cursor: 'pointer',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      transition: 'all 0.2s ease-in-out'
    },
    footerText: {
      marginTop: '36px',
      fontSize: '12px',
      color: '#4b5563',
      letterSpacing: '0.3px',
      display: 'flex',
      alignItems: 'center',
      gap: '6px'
    }
  };

  return (
    <div style={styles.container}>
      {/* Dynamic button animations */}
      <style>{`
        .btn-google:hover {
          background: #f9fafb !important;
          transform: translateY(-1px);
          box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.3) !important;
        }
        .btn-google:active {
          transform: translateY(0);
        }
      `}</style>

      <div style={styles.card}>
        {/* Abstract Minimalist AI/Scheduling Logo Mark */}
        <div style={styles.logoContainer}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 2V5M16 2V5M3.5 9.05H20.5M21 8.5V17C21 19.2091 19.2091 21 17 21H7C4.79086 21 3 19.2091 3 17V8.5C3 6.29086 4.79086 4.5 7 4.5H17C19.2091 4.5 21 6.29086 21 8.5Z" stroke="#ffffff" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="12" cy="14" r="2" fill="#ffffff"/>
          </svg>
        </div>
        
        {/* Heading & Context */}
        <h1 style={styles.title}>AI Meet Scheduler</h1>
        <p style={styles.subtitle}>
          Automated availability and cross-calendar coordination platform.
        </p>

        {/* Clean, Vector-Backed Google Auth Button */}
        <button
          onClick={handleGoogleLogin}
          style={styles.googleBtn}
          className="btn-google"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.47h4.84c-.21 1.12-.84 2.07-1.79 2.7v2.24h2.9c1.69-1.55 2.69-3.85 2.69-6.57z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.47-.8 5.96-2.23l-2.9-2.24c-.8.54-1.84.87-3.06.87-2.35 0-4.35-1.59-5.06-3.73H.96v2.3C2.44 15.93 5.48 18 9 18z" fill="#34A853"/>
            <path d="M3.94 10.67c-.18-.54-.28-1.11-.28-1.67s.1-1.13.28-1.67V5.03H.96C.35 6.24 0 7.59 0 9s.35 2.76.96 3.97l2.98-2.3z" fill="#FBBC05"/>
            <path d="M9 3.58c1.32 0 2.5.45 3.44 1.35L15 2.1C13.46.66 11.42 0 9 0 5.48 0 2.44 2.07.96 5.03l2.98 2.3c.71-2.14 2.71-3.73 5.06-3.73z" fill="#EA4335"/>
          </svg>
          Sign in with Google
        </button>

        {/* Secure Compliance Note */}
        <div style={styles.footerText}>
          <svg width="12" height="14" viewBox="0 0 12 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 1V4.5M6 13C3.5 13 1.5 11 1.5 8.5V5.5C1.5 4 2.5 2.5 4 2V1H8V2C9.5 2.5 10.5 4 10.5 5.5V8.5C10.5 11 8.5 13 6 13Z" stroke="#4b5563" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Secure Enterprise OAuth 2.0
        </div>
      </div>
    </div>
  );
}