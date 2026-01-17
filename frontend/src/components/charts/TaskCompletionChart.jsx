import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { BarChart3 } from 'lucide-react';

export const TaskCompletionChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Calculate REAL activity data from projects
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Get last 7 days
    const days = [];
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      
      const dayStart = new Date(date);
      dayStart.setHours(0, 0, 0, 0);
      const dayEnd = new Date(date);
      dayEnd.setHours(23, 59, 59, 999);
      
      // Count REAL projects created on this day
      const created = projects.filter(p => {
        const createdAt = new Date(p.created_at);
        return createdAt >= dayStart && createdAt <= dayEnd;
      }).length;
      
      // Count REAL projects updated on this day (different from created)
      const updated = projects.filter(p => {
        if (!p.updated_at) return false;
        const updatedAt = new Date(p.updated_at);
        const createdAt = new Date(p.created_at);
        // Only count if update was on this day AND different from creation
        return updatedAt >= dayStart && updatedAt <= dayEnd && 
               (updatedAt.toDateString() !== createdAt.toDateString());
      }).length;
      
      days.push({
        date: dateStr,
        created: created,
        updated: updated,
      });
    }
    
    return days;
  }, [projects]);

  // Calculate totals
  const totals = useMemo(() => {
    if (!chartData.length) return { created: 0, updated: 0 };
    return chartData.reduce((acc, day) => ({
      created: acc.created + day.created,
      updated: acc.updated + day.updated,
    }), { created: 0, updated: 0 });
  }, [chartData]);

  // Check if there's any activity at all
  const hasActivity = totals.created > 0 || totals.updated > 0;

  if (isLoading) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-purple-400" />
            Weekly Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass border-white/10">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-purple-400" />
            Weekly Activity
          </CardTitle>
          <div className="flex gap-6 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              <span className="text-white/60">Created</span>
              <span className="text-white/90 font-medium">{totals.created}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
              <span className="text-white/60">Updated</span>
              <span className="text-white/90 font-medium">{totals.updated}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        {!hasActivity ? (
          <div className="h-[280px] flex flex-col items-center justify-center text-white/40">
            <BarChart3 className="w-12 h-12 mb-3 opacity-30" />
            <p>No activity in the last 7 days</p>
            <p className="text-sm mt-1">Create or update projects to see activity</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#94A3B8' }}
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              />
              <Bar 
                dataKey="created" 
                fill="#A855F7" 
                radius={[4, 4, 0, 0]}
                name="Projects Created"
                maxBarSize={32}
              />
              <Bar 
                dataKey="updated" 
                fill="#06B6D4" 
                radius={[4, 4, 0, 0]}
                name="Projects Updated"
                maxBarSize={32}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};
