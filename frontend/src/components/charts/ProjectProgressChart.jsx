import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { TrendingUp } from 'lucide-react';

// Color palette for project lines
const COLORS = [
  '#A855F7', // Purple
  '#06B6D4', // Cyan
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Violet
  '#EC4899', // Pink
  '#14B8A6', // Teal
];

export const ProjectProgressChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Prepare chart data with one line per project
  const chartData = useMemo(() => {
    if (!projects || projects.length === 0) return { days: [], projects: [] };

    // Use all projects, default progress_percentage to 0 if not set
    const projectsToUse = projects.map(p => ({
      ...p,
      progress_percentage: p.progress_percentage ?? 0
    }));

    // Sort projects by progress (highest first) - closest to launch
    const sortedProjects = [...projectsToUse]
      .sort((a, b) => (b.progress_percentage || 0) - (a.progress_percentage || 0));

    // Generate last 7 days
    const days = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { weekday: 'short' });
      
      const dayData = { date: dateStr };
      
      // For each project, show progress (simulate growth over time)
      sortedProjects.forEach((project) => {
        const createdAt = project.created_at ? new Date(project.created_at) : null;
        const currentProgress = project.progress_percentage || 0;
        
        if (!createdAt) {
          // If no creation date, show current progress for all days
          dayData[`project_${project.id}`] = currentProgress;
        } else if (createdAt > date) {
          // Project doesn't exist yet on this day
          dayData[`project_${project.id}`] = null;
        } else {
          // Project exists - simulate gradual progress growth
          const daysSinceCreation = Math.floor((date - createdAt) / (1000 * 60 * 60 * 24));
          const totalDays = Math.max(1, Math.floor((today - createdAt) / (1000 * 60 * 60 * 24)));
          
          // Simulate linear growth: start at 0, reach current progress over time
          const progressRatio = Math.min(1, daysSinceCreation / totalDays);
          const progress = Math.round(currentProgress * progressRatio);
          
          dayData[`project_${project.id}`] = progress;
        }
      });
      
      days.push(dayData);
    }
    
    return { days, projects: sortedProjects };
  }, [projects]);

  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Project Progress
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

  if (!chartData || !chartData.projects || chartData.projects.length === 0) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Project Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-white/60">
            <p>No project data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="text-xl text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Project Progress
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData.days}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="date" 
              stroke="#9CA3AF"
              style={{ fontSize: 12 }}
            />
            <YAxis 
              stroke="#9CA3AF"
              style={{ fontSize: 12 }}
              domain={[0, 100]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
              }}
            />
            <Legend 
              wrapperStyle={{ color: '#fff', fontSize: '11px' }}
              iconType="line"
            />
            {chartData.projects.map((project, index) => {
              const projectName = project.name || `Project ${project.id}`;
              const color = COLORS[index % COLORS.length];
              const dataKey = `project_${project.id}`;
              
              return (
                <Line
                  key={project.id}
                  type="monotone"
                  dataKey={dataKey}
                  stroke={color}
                  strokeWidth={2.5}
                  dot={{ fill: color, r: 4 }}
                  name={`${projectName} (${project.progress_percentage || 0}%)`}
                  connectNulls
            />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

