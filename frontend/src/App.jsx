import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { Dashboard } from '@/pages/Dashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ProjectDetail from './pages/ProjectDetail';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const renderCountRef = React.useRef(0);

  React.useEffect(() => {
    renderCountRef.current += 1;
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.jsx:21',message:'ProtectedRoute render',data:{isLoading,isAuthenticated,renderCount:renderCountRef.current,path:window.location.pathname},timestamp:Date.now(),sessionId:'debug-session',runId:'run5',hypothesisId:'I'})}).catch(()=>{});
    // #endregion
  }); // This will log every render but won't cause re-renders

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-text-muted">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  const loadUser = useAuthStore((state) => state.loadUser);
  const isLoading = useAuthStore((state) => state.isLoading);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hasLoadedRef = React.useRef(false);

  React.useEffect(() => {
    // Only load user once on mount if:
    // 1. We haven't loaded yet
    // 2. We're in loading state
    // 3. We have a token (don't try to load if no token)
    const token = localStorage.getItem('auth_token');
    if (!hasLoadedRef.current && isLoading && token) {
      hasLoadedRef.current = true;
      loadUser();
    } else if (!token && isLoading) {
      // No token, set loading to false immediately
      useAuthStore.setState({ isLoading: false, isAuthenticated: false });
    }
  }, [isLoading]); // Only depend on isLoading

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project/:id"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

