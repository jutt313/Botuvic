import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { ProjectProgressChart } from '@/components/charts/ProjectProgressChart';
import { TaskCompletionChart } from '@/components/charts/TaskCompletionChart';
import { ProjectsTable } from '@/components/projects/ProjectsTable';
import { NotificationDropdown } from '@/components/notifications/NotificationDropdown';
import { ProfileDropdown } from '@/components/layout/ProfileDropdown';
import { useTerminalTracking } from '@/hooks/useTerminalTracking';

export const Dashboard = () => {
  const { user } = useAuthStore();
  const userName = user?.name || user?.email || 'User';
  
  // Track terminal usage
  useTerminalTracking();

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <header className="dashboard-header">
          <div className="dashboard-welcome">
            <span className="welcome-text">Welcome</span>
            <span className="username-gradient">{userName}</span>
          </div>
          <div className="dashboard-header-actions">
            <NotificationDropdown />
            <ProfileDropdown />
          </div>
        </header>
        <StatsCards />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 px-[25px] mb-6">
          <ProjectProgressChart />
          <TaskCompletionChart />
        </div>
        <div className="px-[25px] mb-6">
          <ProjectsTable />
        </div>
      </div>
    </div>
  );
};

