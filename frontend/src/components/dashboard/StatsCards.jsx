import React from 'react';
import { Rocket, Clock, Activity, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { formatDistanceToNow } from 'date-fns';

export const StatsCards = () => {
  const { user } = useAuthStore();

  // Fetch usage stats from API
  const { data: stats, isLoading } = useQuery({
    queryKey: ['usage-stats'],
    queryFn: async () => {
      try {
        const response = await api.get('/usage/stats');
        return response.data;
      } catch (error) {
        // Return mock data if API not ready
        return {
          projects_built: 0,
          total_usage_hours: 0,
          total_sessions: 0,
          last_activity: null
        };
      }
    },
    refetchInterval: 30000, // Refresh every 30s
  });

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

  const {
    projects_built = 0,
    total_usage_hours = 0,
    total_sessions = 0,
    last_activity = null
  } = stats || {};

  // Format last activity
  const lastActivityText = last_activity
    ? formatDistanceToNow(new Date(last_activity), { addSuffix: true })
    : 'No activity yet';

  const cards = [
    {
      title: 'Projects Built',
      value: projects_built,
      subtitle: 'Total projects created',
      icon: Rocket,
      iconColor: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
    {
      title: 'Total Usage',
      value: total_usage_hours > 0 ? `${total_usage_hours}h` : '0',
      subtitle: 'Time using BOTUVIC',
      icon: Clock,
      iconColor: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
    },
    {
      title: 'Total Sessions',
      value: total_sessions,
      subtitle: 'MCP activations',
      icon: Activity,
      iconColor: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'Last Activity',
      value: lastActivityText,
      subtitle: 'Most recent use',
      icon: Calendar,
      iconColor: 'text-pink-400',
      bgColor: 'bg-pink-500/10',
      isTime: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 px-[25px] mb-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div
            key={index}
            className="glass rounded-lg p-5 border border-white/10 hover:border-white/20 transition-all duration-200 hover:scale-[1.02] group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className={`p-2.5 rounded-lg ${card.bgColor} group-hover:scale-110 transition-transform duration-200`}>
                  <Icon className={`w-5 h-5 ${card.iconColor}`} strokeWidth={1.5} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-white/60 mb-1 uppercase tracking-wide">{card.title}</p>
                <p className={`${card.isTime ? 'text-xl' : 'text-2xl'} font-bold text-white mb-1 truncate`}>
                  {card.value}
                </p>
                <p className="text-xs text-white/50">{card.subtitle}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

