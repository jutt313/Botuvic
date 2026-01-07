import { useEffect } from 'react';
import { useNotificationStore, notificationTypes } from '@/store/notificationStore';

let terminalSessionStart = null;
let terminalSessionInterval = null;

export const useTerminalTracking = () => {
  const addNotification = useNotificationStore((state) => state.addNotification);

  useEffect(() => {
    // Track terminal usage - simulate by checking if user is active
    // In a real app, this would come from backend/CLI sync
    const startTerminalSession = () => {
      if (!terminalSessionStart) {
        terminalSessionStart = new Date();
        
        // Check for terminal sessions every 5 minutes
        terminalSessionInterval = setInterval(() => {
          if (terminalSessionStart) {
            const now = new Date();
            const duration = Math.floor((now - terminalSessionStart) / 1000 / 60); // minutes
            
            // Only notify if session is longer than 5 minutes
            if (duration >= 5) {
              addNotification({
                type: notificationTypes.PROJECT_ACCESSED,
                title: 'Terminal Session Active',
                message: `Terminal session active from ${terminalSessionStart.toLocaleTimeString()} to ${now.toLocaleTimeString()}`,
                details: {
                  startTime: terminalSessionStart.toISOString(),
                  endTime: now.toISOString(),
                  duration: `${duration} minutes`,
                },
              });
              
              // Reset for next session
              terminalSessionStart = null;
            }
          }
        }, 5 * 60 * 1000); // Check every 5 minutes
      }
    };

    // Simulate terminal activity detection
    // In real app, this would listen to CLI events or API calls
    const handleActivity = () => {
      startTerminalSession();
    };

    // Listen for any activity that might indicate terminal usage
    window.addEventListener('focus', handleActivity);
    document.addEventListener('click', handleActivity);
    document.addEventListener('keydown', handleActivity);

    return () => {
      window.removeEventListener('focus', handleActivity);
      document.removeEventListener('click', handleActivity);
      document.removeEventListener('keydown', handleActivity);
      if (terminalSessionInterval) {
        clearInterval(terminalSessionInterval);
      }
    };
  }, [addNotification]);
};

// Function to manually track terminal session (can be called from CLI sync)
export const trackTerminalSession = (startTime, endTime) => {
  const store = useNotificationStore.getState();
  
  const start = new Date(startTime);
  const end = new Date(endTime);
  const duration = Math.floor((end - start) / 1000 / 60); // minutes
  
  store.addNotification({
    type: notificationTypes.PROJECT_ACCESSED,
    title: 'Terminal Session Recorded',
    message: `Terminal used from ${start.toLocaleTimeString()} to ${end.toLocaleTimeString()} (${duration} minutes)`,
    details: {
      startTime: start.toISOString(),
      endTime: end.toISOString(),
      duration: `${duration} minutes`,
    },
  });
};

