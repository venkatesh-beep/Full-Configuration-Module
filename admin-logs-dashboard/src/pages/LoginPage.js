import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { handleAdminShortcutLogin, normalLogin } from '../services/logService';

function LoginPage() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const adminResult = handleAdminShortcutLogin(credentials.username, credentials.password);

    if (adminResult.isAdmin) {
      console.debug('[Login] Admin redirect to /admin-logs triggered successfully.');
      navigate('/admin-logs');
      return;
    }

    try {
      await normalLogin(adminResult.username, adminResult.password);
      console.debug('[Login] Normal login success. Non-admin remains on app home.');
      localStorage.setItem('isAdmin', 'false');
      localStorage.setItem('authUser', adminResult.username);
      setError('Normal login succeeded. Admin dashboard is restricted to Logs@BT.');
    } catch (err) {
      console.debug('[Login] Normal login failed:', err.message);
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="auth-wrap">
      <form className="card" onSubmit={onSubmit}>
        <h2>Login</h2>
        <input
          placeholder="Username"
          value={credentials.username}
          onChange={(e) => setCredentials((v) => ({ ...v, username: e.target.value }))}
        />
        <input
          type="password"
          placeholder="Password"
          value={credentials.password}
          onChange={(e) => setCredentials((v) => ({ ...v, password: e.target.value }))}
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default LoginPage;
