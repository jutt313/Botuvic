import { create } from 'zustand';
import { authService } from '@/services/auth';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isLoadUserRunning: false,

  login: async (email, password) => {
    try {
      const { token, user } = await authService.login(email, password);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.js:11',message:'Login successful, updating store',data:{hasUser:!!user,hasToken:!!token,isAuthenticated:true},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
      set({ user, isAuthenticated: true, isLoading: false });
      return user;
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    await authService.logout();
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    // Prevent multiple simultaneous calls
    if (get().isLoadUserRunning) {
      return;
    }
    
    set({ isLoadUserRunning: true });
    
    // #region agent log
    const tokenBefore = localStorage.getItem('auth_token');
    fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.js:24',message:'loadUser called',data:{hasToken:!!tokenBefore,tokenLength:tokenBefore?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run4',hypothesisId:'G'})}).catch(()=>{});
    // #endregion
    try {
      const user = await authService.getCurrentUser();
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.js:27',message:'loadUser success',data:{hasUser:!!user},timestamp:Date.now(),sessionId:'debug-session',runId:'run4',hypothesisId:'G'})}).catch(()=>{});
      // #endregion
      set({ user, isAuthenticated: true, isLoading: false, isLoadUserRunning: false });
    } catch (error) {
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.js:29',message:'loadUser error',data:{errorMessage:error.message,errorStatus:error.response?.status},timestamp:Date.now(),sessionId:'debug-session',runId:'run4',hypothesisId:'G'})}).catch(()=>{});
      // #endregion
      set({ user: null, isAuthenticated: false, isLoading: false, isLoadUserRunning: false });
    }
  },

  updateUser: (updates) => {
    set((state) => ({
      user: { ...state.user, ...updates },
    }));
  },
}));

