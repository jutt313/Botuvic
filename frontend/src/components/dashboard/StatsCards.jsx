import React from 'react';
import { Folder, CheckCircle2, Clock, TrendingUp } from 'lucide-react';
import { useProjects } from '@/hooks/useProjects';
import { formatDistanceToNow } from 'date-fns';

export const StatsCards = () => {
  const { data: projects = [], isLoading } = useProjects();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 px-[25px] mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass rounded-lg p-5 animate-pulse">
            <div className="h-5 bg-white/10 rounded w-20 mb-4"></div>
            <div className="h-10 bg-white/10 rounded w-16 mb-2"></div>
            <div className="h-4 bg-white/10 rounded w-24"></div>
          </div>
        ))}
      </div>
    );
  }

  // Calculate stats
  const totalProjects = projects.length;
  
  // Projects created this week
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  const newThisWeek = projects.filter(p => {
    const createdAt = p.created_at ? new Date(p.created_at) : null;
    return createdAt && createdAt >= oneWeekAgo;
  }).length;

  // Active tasks (projects with active/in_progress status)
  const activeProjects = projects.filter(p => 
    p.status === 'active' || p.status === 'in_progress' || !p.status
  );
  const activeTasksCount = activeProjects.length;
  const avgProgress = activeProjects.length > 0
    ? Math.round(
        activeProjects.reduce((sum, p) => sum + (p.progress_percentage || 0), 0) / 
        activeProjects.length
      )
    : 0;

  // Recent activity (most recent updated_at)
  const recentActivity = projects
    .map(p => p.updated_at || p.created_at)
    .filter(Boolean)
    .sort((a, b) => new Date(b) - new Date(a))[0];

  // Success rate (average phase completion)
  const successRate = projects.length > 0
    ? Math.round(
        projects.reduce((sum, p) => {
          const currentPhase = p.current_phase || 1;
          const totalPhases = p.total_phases || 3;
          return sum + (currentPhase / totalPhases) * 100;
        }, 0) / projects.length
      )
    : 0;

  const cards = [
    {
      title: 'Projects',
      value: totalProjects,
      subtitle: `+${newThisWeek} this week`,
      icon: Folder,
      color: 'from-purple-500 to-purple-600',
    },
    {
      title: 'Active Tasks',
      value: activeTasksCount,
      subtitle: `${avgProgress}% avg progress`,
      icon: CheckCircle2,
      color: 'from-cyan-500 to-cyan-600',
    },
    {
      title: 'Recent Activity',
      value: recentActivity 
        ? formatDistanceToNow(new Date(recentActivity), { addSuffix: true })
        : 'No activity',
      subtitle: 'Last update',
      icon: Clock,
      color: 'from-green-500 to-green-600',
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      subtitle: 'Phase completion',
      icon: TrendingUp,
      color: 'from-pink-500 to-pink-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 px-[25px] mb-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div
            key={index}
            className="glass rounded-lg p-5 border border-white/10 hover:border-white/20 transition-all duration-200"
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <Icon className="w-6 h-6 text-white/80" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base text-white/70 mb-2">{card.title}</p>
                <p className="text-3xl font-bold text-white mb-2 truncate">
                  {card.value}
                </p>
                <p className="text-sm text-white/60">{card.subtitle}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

