import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { ListTodo } from 'lucide-react';

export const TaskCompletionChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Prepare stacked bar data for each project
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Get top 8 most recent projects for the chart
    return [...projects]
      .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
      .slice(0, 8)
      .map(p => {
        const progress = p.progress_percentage || 0;
        const currentPhase = p.current_phase || 1;
        const totalPhases = p.total_phases || 1;
        const phasesCompleted = Math.max(0, currentPhase - 1);
        const phasesRemaining = totalPhases - currentPhase;
        
        return {
          name: p.name.length > 8 ? p.name.substring(0, 8) + '..' : p.name,
          fullName: p.name,
          progress: progress,
          remaining: 100 - progress,
          phasesCompleted: phasesCompleted,
          currentPhase: 1, // Current phase (always 1 for visualization)
          phasesRemaining: phasesRemaining,
          totalPhases: totalPhases,
          status: p.status || 'active',
        };
      });
  }, [projects]);

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!projects.length) return { avgProgress: 0, completed: 0 };
    const totalProgress = projects.reduce((sum, p) => sum + (p.progress_percentage || 0), 0);
    const avgProgress = Math.round(totalProgress / projects.length);
    const completed = projects.filter(p => (p.status || '').toLowerCase() === 'complete').length;
    return { avgProgress, completed };
  }, [projects]);

  if (isLoading) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <ListTodo className="w-4 h-4 text-purple-400" />
            Project Progress
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

  if (!projects.length) {
    return (
      <Card className="glass border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-white/90 flex items-center gap-2">
            <ListTodo className="w-4 h-4 text-purple-400" />
            Project Progress
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
            <ListTodo className="w-4 h-4 text-purple-400" />
            Project Progress
          </CardTitle>
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
              <span className="text-white/60">Done</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              <span className="text-white/60">Remaining</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-white/60">Avg</span>
              <span className="text-white font-medium">{stats.avgProgress}%</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart 
            data={chartData} 
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="name"
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              domain={[0, 100]}
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#E2E8F0', fontWeight: 'bold', marginBottom: '4px' }}
              formatter={(value, name, props) => {
                if (name === 'progress') return [`${value}%`, 'Completed'];
                if (name === 'remaining') return [`${value}%`, 'Remaining'];
                return [value, name];
              }}
              labelFormatter={(label, payload) => {
                if (payload && payload[0]) {
                  const data = payload[0].payload;
                  return `${data.fullName} (Phase ${data.currentPhase + data.phasesCompleted}/${data.totalPhases})`;
                }
                return label;
              }}
            />
            {/* Stacked bars: Progress (done) + Remaining */}
            <Bar 
              dataKey="progress" 
              stackId="a"
              fill="#06B6D4"
              radius={[0, 0, 0, 0]}
              maxBarSize={40}
              name="progress"
            />
            <Bar 
              dataKey="remaining" 
              stackId="a"
              fill="#A855F7"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
              name="remaining"
              fillOpacity={0.4}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
