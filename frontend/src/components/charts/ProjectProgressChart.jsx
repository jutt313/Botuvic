import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { TrendingUp } from 'lucide-react';

export const ProjectProgressChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Generate clean weekly data
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    const days = [];
    const today = new Date();
    
    // Get top 3 projects by recent activity
    const topProjects = [...projects]
      .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
      .slice(0, 3);

    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      
      const dayData = { date: dateStr };
      
      topProjects.forEach((project, idx) => {
        const progress = project.progress_percentage || 0;
        // Simulate gradual growth
        const factor = (7 - i) / 7;
        dayData[`p${idx}`] = Math.round(progress * factor);
      });
      
      days.push(dayData);
    }
    
    return { days, projects: topProjects };
  }, [projects]);

  if (isLoading) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Progress
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

  if (!chartData.days || chartData.days.length === 0) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] flex items-center justify-center text-white/40">
            No project data yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const colors = ['#06B6D4', '#A855F7', '#10B981']; // Cyan, Purple, Green

  return (
    <Card className="glass border-white/10">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Project Progress
          </CardTitle>
          <div className="flex gap-4 text-xs">
            {chartData.projects.slice(0, 3).map((p, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[i] }}></div>
                <span className="text-white/60 truncate max-w-[80px]">{p.name}</span>
              </div>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData.days} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#94A3B8' }}
              formatter={(value) => [`${value}%`, 'Progress']}
            />
            {chartData.projects.slice(0, 3).map((_, i) => (
              <Line
                key={i}
                type="monotone"
                dataKey={`p${i}`}
                stroke={colors[i]}
                strokeWidth={2}
                dot={{ fill: colors[i], r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
