import axios from 'axios';

export default function Login() {

  const handleGoogleLogin = async () => {
    try {

      const res = await axios.get(
        'http://127.0.0.1:8000/api/auth/login'
      );

      window.location.href = res.data.authorization_url;

    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to start Google login');
    }
  };

  return (
    <div>
      <button onClick={handleGoogleLogin}>
        Login with Google
      </button>
    </div>
  );
}