import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useNotificationStore, notificationTypes } from '@/store/notificationStore';
import './Auth.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const callbackUrl = searchParams.get('callback');
  const cliSession = searchParams.get('cli_session');
  const [cliSuccess, setCliSuccess] = useState(false);
  const login = useAuthStore((state) => state.login);
  const addNotification = useNotificationStore((state) => state.addNotification);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);

      // Add login notification
      addNotification({
        type: notificationTypes.LOGIN_DETECTED,
        title: 'Login Successful',
        message: `Welcome back! You logged in at ${new Date().toLocaleTimeString()}.`,
        details: {
          email: email,
          loginTime: new Date().toISOString(),
          source: cliSession ? 'CLI' : 'Web',
        },
      });

      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Login.jsx:22',message:'Login successful, checking redirect',data:{hasCallback:!!callbackUrl,hasCLI:!!cliSession},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion

      const token = localStorage.getItem('auth_token');

      // Debug logging
      console.log('=== CLI Session Debug ===');
      console.log('CLI Session ID:', cliSession);
      console.log('Token exists:', !!token);
      console.log('Token value:', token?.substring(0, 20) + '...');

      // If CLI session exists, send token to backend
      if (cliSession && token) {
        try {
          const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          console.log('Sending token to backend:', `${backendUrl}/api/auth/cli-session`);

          const response = await fetch(`${backendUrl}/api/auth/cli-session`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              session_id: cliSession,
              token: token
            })
          });

          console.log('Backend response status:', response.status);
          const responseData = await response.text();
          console.log('Backend response:', responseData);

          if (response.ok) {
            setCliSuccess(true);
            setLoading(false);
            return;
          } else {
            console.error('Backend returned error:', response.status, responseData);
          }
        } catch (cliError) {
          console.error('Failed to send token to CLI:', cliError);
        }
      } else {
        console.log('CLI session or token missing - skipping CLI flow');
      }

      // If callback URL exists, redirect with token
      if (callbackUrl) {
        if (token) {
          const callback = new URL(callbackUrl);
          callback.searchParams.set('token', token);
          callback.searchParams.set('email', email);
          window.location.href = callback.toString();
        } else {
          // #region agent log
          fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Login.jsx:33',message:'Navigating to / (no token)',data:{targetPath:'/'},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
          // #endregion
          navigate('/');
        }
      } else {
        // Let ProfileGuard handle the profile check
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Login.jsx:36',message:'Navigating to / (no callback)',data:{targetPath:'/'},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  // If CLI login successful, show success message
  if (cliSuccess) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
            <h1 className="auth-title" style={{ color: '#A855F7' }}>Login Successful!</h1>
            <p className="auth-subtitle" style={{ marginTop: '1rem' }}>
              You can now return to your terminal.
            </p>
            <p style={{ marginTop: '2rem', color: '#64748B', fontSize: '0.875rem' }}>
              This window can be closed.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Welcome Back</h1>
        <p className="auth-subtitle">Sign in to continue to BOTUVIC</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="your@email.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          <Link to="/forgot-password" className="forgot-link">
            Forgot password?
          </Link>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/signup" className="auth-link">Sign up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;

