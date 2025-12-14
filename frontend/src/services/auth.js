import api from './api';

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user } = response.data;
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'auth.js:5',message:'Login response received',data:{hasAccessToken:!!access_token,hasUser:!!user,responseKeys:Object.keys(response.data)},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'F'})}).catch(()=>{});
    // #endregion
    if (access_token) {
      localStorage.setItem('auth_token', access_token);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'auth.js:8',message:'Token saved to localStorage',data:{tokenLength:access_token.length,tokenPrefix:access_token.substring(0,20)},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
    }
    return { token: access_token, user };
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      localStorage.removeItem('auth_token');
    }
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.patch('/auth/profile', data);
    return response.data;
  },
};
