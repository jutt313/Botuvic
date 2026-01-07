import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { CheckCircle2 } from 'lucide-react';

export const TaskCompletionChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Prepare chart data with one bar per project
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Calculate tasks for each project
    const projectData = projects.map((project) => {
      // Estimate total tasks based on phases (default: 10 tasks per phase)
      const totalPhases = project.total_phases || 3;
      const totalTasks = totalPhases * 10; // Estimate 10 tasks per phase
      
      // Calculate completed tasks based on progress percentage
      const progress = project.progress_percentage || 0;
      const completedTasks = Math.round((progress / 100) * totalTasks);
      
      return {
        name: project.name || `Project ${project.id}`,
        totalTasks: totalTasks,
        completedTasks: completedTasks,
        progress: progress,
      };
    });

    // Sort by progress (highest first) - closest to completion
    return projectData.sort((a, b) => b.progress - a.progress);
  }, [projects]);

  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Task Completion
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (projects.length === 0 || chartData.length === 0) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Task Completion
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-white/60">
            <p>No task data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Color function for total tasks bar - consistent color for all
  const getBarColor = () => {
    return '#EF4444'; // Red - consistent color for all total tasks
  };

  const getCompletedBarColor = (progress) => {
    if (progress >= 80) return '#10B981'; // Green
    if (progress >= 50) return '#06B6D4'; // Cyan
    if (progress >= 25) return '#F59E0B'; // Amber
    return '#EF4444'; // Red
  };

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="text-xl text-white flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" />
          Task Completion
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart 
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              type="number"
              stroke="#9CA3AF"
              style={{ fontSize: 12 }}
            />
            <YAxis 
              type="category"
              dataKey="name"
              stroke="#9CA3AF"
              style={{ fontSize: 11 }}
              width={120}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: '#fff',
              }}
              formatter={(value, name) => {
                if (name === 'totalTasks') return [value, 'Total Tasks'];
                if (name === 'completedTasks') return [value, 'Completed Tasks'];
                return [value, name];
              }}
              labelStyle={{ color: '#A855F7', fontWeight: 'bold' }}
            />
            <Legend 
              wrapperStyle={{ color: '#fff', fontSize: '12px' }}
            />
            <Bar 
              dataKey="totalTasks" 
              name="Total Tasks"
              fill="#6B7280"
              radius={[0, 4, 4, 0]}
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-total-${index}`} 
                  fill={getBarColor()}
                />
              ))}
            </Bar>
            <Bar 
              dataKey="completedTasks" 
              name="Completed Tasks"
              fill="#10B981"
              radius={[0, 4, 4, 0]}
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-completed-${index}`} 
                  fill={getCompletedBarColor(entry.progress)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

