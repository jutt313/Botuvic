import React from 'react';
import { MetricsCard } from './MetricsCard';
import { Folder, CheckCircle, Zap, AlertCircle } from 'lucide-react';
import { useMetrics } from '@/hooks/useProjects';

export const MetricsGrid = () => {
  const { data: metrics, isLoading, error } = useMetrics();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-surface rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-24 mb-4"></div>
            <div className="h-8 bg-white/10 rounded w-16 mb-2"></div>
            <div className="h-4 bg-white/10 rounded w-20"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-surface rounded-lg p-6 border border-error/50">
        <p className="text-error">Failed to load metrics. Please try again later.</p>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricsCard
        title="Total Projects"
        value={metrics.totalProjects || 0}
        icon={Folder}
      />

      <MetricsCard
        title="Tasks Completed"
        value={metrics.tasksCompleted || 0}
        icon={CheckCircle}
      />

      <MetricsCard
        title="AI API Calls"
        value={metrics.aiCalls?.toLocaleString() || 0}
        icon={Zap}
      />

      <MetricsCard
        title="Errors Fixed"
        value={metrics.errorsFixed || 0}
        icon={AlertCircle}
      />
    </div>
  );
};

