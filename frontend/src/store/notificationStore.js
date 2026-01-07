import { create } from 'zustand';

const notificationTypes = {
  PROJECT_CREATED: 'project_created',
  PROJECT_DELETED: 'project_deleted',
  PROJECT_UPDATED: 'project_updated',
  PROJECT_STATUS_CHANGED: 'project_status_changed',
  PROJECT_PROGRESS_UPDATED: 'project_progress_updated',
  PROJECT_ARCHIVED: 'project_archived',
  PHASE_COMPLETED: 'phase_completed',
  TASK_COMPLETED: 'task_completed',
  PHASE_STARTED: 'phase_started',
  TASK_CREATED: 'task_created',
  TASK_DELETED: 'task_deleted',
  SUBSCRIPTION_ENDED: 'subscription_ended',
  PAYMENT_ACCEPTED: 'payment_accepted',
  PAYMENT_DECLINED: 'payment_declined',
  SUBSCRIPTION_RENEWED: 'subscription_renewed',
  SUBSCRIPTION_CANCELLED: 'subscription_cancelled',
  SUBSCRIPTION_UPGRADED: 'subscription_upgraded',
  SUBSCRIPTION_DOWNGRADED: 'subscription_downgraded',
  PAYMENT_REMINDER: 'payment_reminder',
  TRIAL_ENDING: 'trial_ending',
  LLM_ADDED: 'llm_added',
  LLM_DELETED: 'llm_deleted',
  LLM_UPDATED: 'llm_updated',
  LLM_DEFAULT_CHANGED: 'llm_default_changed',
  LLM_QUOTA_EXCEEDED: 'llm_quota_exceeded',
  LLM_CONNECTION_FAILED: 'llm_connection_failed',
  SYNC_COMPLETED: 'sync_completed',
  SYNC_FAILED: 'sync_failed',
  SYNC_STARTED: 'sync_started',
  FILES_SYNCED: 'files_synced',
  SETTINGS_UPDATED: 'settings_updated',
  PROFILE_UPDATED: 'profile_updated',
  PASSWORD_CHANGED: 'password_changed',
  EMAIL_CHANGED: 'email_changed',
  BUILD_FAILED: 'build_failed',
  ERROR_DETECTED: 'error_detected',
  WARNING_DETECTED: 'warning_detected',
  API_ERROR: 'api_error',
  PROJECT_ACCESSED: 'project_accessed',
  REPORT_GENERATED: 'report_generated',
  EXPORT_COMPLETED: 'export_completed',
  IMPORT_COMPLETED: 'import_completed',
  LOGIN_DETECTED: 'login_detected',
  SESSION_EXPIRED: 'session_expired',
  UNAUTHORIZED_ACCESS: 'unauthorized_access',
};

const getNotificationIcon = (type) => {
  if (type.includes('project')) return '📁';
  if (type.includes('payment') || type.includes('subscription')) return '💳';
  if (type.includes('llm') || type.includes('api')) return '🤖';
  if (type.includes('sync')) return '🔄';
  if (type.includes('error') || type.includes('failed')) return '❌';
  if (type.includes('warning')) return '⚠️';
  if (type.includes('task') || type.includes('phase')) return '✅';
  if (type.includes('login') || type.includes('session')) return '🔐';
  return '🔔';
};

const getNotificationColor = (type) => {
  if (type.includes('error') || type.includes('failed') || type.includes('declined')) return 'text-red-400';
  if (type.includes('warning')) return 'text-yellow-400';
  if (type.includes('success') || type.includes('completed') || type.includes('accepted')) return 'text-green-400';
  if (type.includes('payment') || type.includes('subscription')) return 'text-purple-400';
  return 'text-blue-400';
};

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  
  addNotification: (notification) => {
    const newNotification = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      type: notification.type,
      title: notification.title,
      message: notification.message,
      details: notification.details || null,
      timestamp: new Date().toISOString(),
      read: false,
      expanded: false,
      icon: getNotificationIcon(notification.type),
      color: getNotificationColor(notification.type),
    };
    
    set((state) => ({
      notifications: [newNotification, ...state.notifications].slice(0, 100), // Keep last 100
    }));
  },
  
  markAsRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    }));
  },
  
  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    }));
  },
  
  deleteNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },
  
  deleteAllNotifications: () => {
    set({ notifications: [] });
  },
  
  toggleExpand: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, expanded: !n.expanded } : n
      ),
    }));
  },
  
  getUnreadCount: () => {
    return get().notifications.filter((n) => !n.read).length;
  },
}));

export { notificationTypes };

