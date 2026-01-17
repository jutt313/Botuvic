import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { ListTodo } from 'lucide-react';

export const TaskCompletionChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Prepare project progress data
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Get top 10 most recent projects for the chart
    return [...projects]
      .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
      .slice(0, 10)
      .map(p => ({
        name: p.name.length > 12 ? p.name.substring(0, 12) + '...' : p.name,
        fullName: p.name,
        progress: p.progress_percentage || 0,
        currentPhase: p.current_phase || 1,
        totalPhases: p.total_phases || 1,
        phaseProgress: Math.round(((p.current_phase || 1) / (p.total_phases || 1)) * 100),
        status: p.status || 'active',
      }));
  }, [projects]);

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!projects.length) return { avgProgress: 0, totalPhases: 0, completed: 0 };
    
    const totalProgress = projects.reduce((sum, p) => sum + (p.progress_percentage || 0), 0);
    const avgProgress = Math.round(totalProgress / projects.length);
    const totalPhases = projects.reduce((sum, p) => sum + (p.total_phases || 1), 0);
    const completedPhases = projects.reduce((sum, p) => sum + (p.current_phase || 1) - 1, 0);
    const completed = projects.filter(p => (p.status || '').toLowerCase() === 'complete').length;
    
    return { avgProgress, totalPhases, completedPhases, completed };
  }, [projects]);

  // Color based on progress
  const getProgressColor = (progress) => {
    if (progress >= 75) return '#10B981'; // Green
    if (progress >= 50) return '#22C55E'; // Light green
    if (progress >= 25) return '#EAB308'; // Yellow
    return '#F59E0B'; // Orange
  };

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
              <span className="text-white/60">Avg Progress</span>
              <span className="text-white font-medium">{stats.avgProgress}%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-white/60">Completed</span>
              <span className="text-white font-medium">{stats.completed}/{projects.length}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart 
            data={chartData} 
            layout="vertical" 
            margin={{ top: 5, right: 30, left: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
            <XAxis 
              type="number" 
              domain={[0, 100]}
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <YAxis 
              type="category" 
              dataKey="name"
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#E2E8F0', fontWeight: 'bold' }}
              formatter={(value, name, props) => {
                const data = props.payload;
                return [
                  <div key="tooltip" className="space-y-1">
                    <div>Progress: <span className="text-cyan-400 font-medium">{data.progress}%</span></div>
                    <div>Phase: <span className="text-purple-400 font-medium">{data.currentPhase}/{data.totalPhases}</span></div>
                    <div>Status: <span className="text-emerald-400 font-medium">{data.status}</span></div>
                  </div>,
                  ''
                ];
              }}
              labelFormatter={(label, payload) => payload[0]?.payload?.fullName || label}
            />
            <Bar 
              dataKey="progress" 
              radius={[0, 4, 4, 0]}
              maxBarSize={20}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getProgressColor(entry.progress)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        
        {/* Phase indicators below chart */}
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="flex flex-wrap gap-2 text-xs">
            {chartData.slice(0, 5).map((p, i) => (
              <div key={i} className="flex items-center gap-2 bg-white/5 rounded px-2 py-1">
                <span className="text-white/70 truncate max-w-[60px]">{p.name}</span>
                <span className="text-purple-400">P{p.currentPhase}/{p.totalPhases}</span>
                <span className="text-cyan-400">{p.progress}%</span>
              </div>
            ))}
            {chartData.length > 5 && (
              <span className="text-white/40 px-2 py-1">+{chartData.length - 5} more</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
