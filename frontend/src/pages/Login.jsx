import axios from 'axios';

export default function Login() {

  // const handleGoogleLogin = async () => {
  //   try {

  //     const res = await axios.get(
  //       'http://127.0.0.1:8000/api/auth/login'
  //     );

  //     window.location.href = res.data.authorization_url;

  //   } catch (error) {
  //     console.error('Login error:', error);
  //     alert('Failed to start Google login');
  //   }
  // };
  const handleGoogleLogin = async () => {
    try {
      // Add withCredentials: true to allow the session cookie to be saved
      // const res = await axios.get(
      //   'http://127.0.0.1:8000/api/auth/login',
      //   { withCredentials: true } 
      // );
      const res = await axios.get(
  'http://localhost:8000/api/auth/login', // Change 127.0.0.1 to localhost
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

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: 'lightblue'
      }}
    >
      <h1 style={{ color: 'black' }}>
        AI Meet Scheduler
      </h1>

      <p style={{ color: 'black' }}>
        Smart Meeting Scheduling Powered By AI
      </p>

      <button
        onClick={handleGoogleLogin}
        style={{
          padding: '10px 20px',
          fontSize: '18px',
          cursor: 'pointer'
        }}
      >
        Login with Google
      </button>
    </div>
  );
}