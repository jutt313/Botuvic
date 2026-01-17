import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { TrendingUp } from 'lucide-react';

export const ProjectProgressChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Generate data showing project growth over time
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Find date range
    const dates = projects.map(p => new Date(p.created_at));
    const earliestDate = new Date(Math.min(...dates));
    const today = new Date();
    
    const diffDays = Math.ceil((today - earliestDate) / (1000 * 60 * 60 * 24));
    const step = Math.max(1, Math.floor(diffDays / 20)); // Max 20 points
    
    const data = [];
    
    for (let i = 0; i <= diffDays; i += step) {
      const date = new Date(earliestDate);
      date.setDate(date.getDate() + i);
      
      const total = projects.filter(p => new Date(p.created_at) <= date).length;
      const active = projects.filter(p => {
        const created = new Date(p.created_at);
        const status = (p.status || '').toLowerCase();
        return created <= date && ['in_progress', 'active', 'new'].includes(status);
      }).length;
      const completed = projects.filter(p => {
        const created = new Date(p.created_at);
        const status = (p.status || '').toLowerCase();
        return created <= date && ['complete', 'completed'].includes(status);
      }).length;
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        Total: total,
        Active: active,
        Completed: completed,
      });
    }
    
    return data;
  }, [projects]);

  const total = projects.length;
  const active = projects.filter(p => ['in_progress', 'active', 'new'].includes((p.status || '').toLowerCase())).length;
  const completed = projects.filter(p => ['complete', 'completed'].includes((p.status || '').toLowerCase())).length;

  if (isLoading) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!projects.length) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] flex items-center justify-center text-white/40">
            No projects yet
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
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Overview
          </CardTitle>
          <div className="flex gap-4 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span className="text-white/60">Total</span>
              <span className="text-white font-medium">{total}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              <span className="text-white/60">Active</span>
              <span className="text-white font-medium">{active}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-white/60">Done</span>
              <span className="text-white font-medium">{completed}</span>
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis 
              dataKey="date" 
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
            />
            <YAxis 
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              domain={[0, 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
              }}
            />
            <Line 
              type="monotone" 
              dataKey="Total" 
              stroke="#06B6D4" 
              strokeWidth={3}
              dot={{ r: 4, fill: '#06B6D4' }}
            />
            <Line 
              type="monotone" 
              dataKey="Active" 
              stroke="#A855F7" 
              strokeWidth={3}
              strokeDasharray="8 4"
              dot={{ r: 4, fill: '#A855F7' }}
            />
            <Line 
              type="monotone" 
              dataKey="Completed" 
              stroke="#10B981" 
              strokeWidth={3}
              dot={{ r: 4, fill: '#10B981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
