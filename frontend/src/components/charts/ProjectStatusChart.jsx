import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { Folder } from 'lucide-react';

export const ProjectStatusChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <Folder className="w-5 h-5" />
            Project Status
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

  // Calculate status distribution
  const statusCounts = {
    active: 0,
    paused: 0,
    complete: 0,
    new: 0,
  };

  projects.forEach(project => {
    const status = project.status || 'new';
    if (statusCounts.hasOwnProperty(status)) {
      statusCounts[status]++;
    } else {
      statusCounts.active++;
    }
  });

  const data = [
    { name: 'Active', value: statusCounts.active, color: '#A855F7' },
    { name: 'New', value: statusCounts.new, color: '#06B6D4' },
    { name: 'Paused', value: statusCounts.paused, color: '#F59E0B' },
    { name: 'Complete', value: statusCounts.complete, color: '#10B981' },
  ].filter(item => item.value > 0);

  if (projects.length === 0 || data.length === 0) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <Folder className="w-5 h-5" />
            Project Status
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
          <Folder className="w-5 h-5" />
          Project Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
              }}
            />
            <Legend 
              wrapperStyle={{ color: '#fff', fontSize: '12px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};













