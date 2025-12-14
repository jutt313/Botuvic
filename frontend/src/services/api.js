import axios from 'axios';

// Use relative URL to leverage Vite proxy, or absolute if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// #region agent log
fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.js:4',message:'API service initialized',data:{API_BASE_URL,VITE_API_URL:import.meta.env.VITE_API_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'C'})}).catch(()=>{});
// #endregion

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.js:14',message:'API request interceptor',data:{url:config.url,baseURL:config.baseURL,fullUrl:`${config.baseURL}${config.url}`,method:config.method,hasToken:!!token,tokenLength:token?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'F'})}).catch(()=>{});
    // #endregion
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Only redirect on 401 if we're not already on login/signup page
    // AND if it's not a metrics endpoint (metrics might fail for other reasons)
    const isAuthPage = ['/login', '/signup', '/forgot-password'].includes(window.location.pathname);
    const isMetricsEndpoint = error.config?.url?.includes('/metrics');
    
    if (error.response?.status === 401 && !isAuthPage) {
      // Don't redirect for metrics 401 - just let it fail gracefully
      if (!isMetricsEndpoint) {
        localStorage.removeItem('auth_token');
        // Use replace to avoid adding to history
        window.location.replace('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default api;

