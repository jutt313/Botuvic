import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { TrendingUp } from 'lucide-react';

export const ProjectProgressChart = () => {
  const { data: projects = [], isLoading } = useProjects();

  // Calculate status distribution for ALL projects
  const statusData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    // Count projects by status
    const statusCounts = {};

    projects.forEach(p => {
      const status = (p.status || 'active').toLowerCase().replace('_', ' ');
      // Normalize status names
      let displayStatus = status;
      if (status === 'new') displayStatus = 'active';
      if (status === 'in progress') displayStatus = 'in progress';
      
      statusCounts[displayStatus] = (statusCounts[displayStatus] || 0) + 1;
    });

    const colors = {
      'active': '#10B981',
      'in progress': '#06B6D4',
      'in_progress': '#06B6D4',
      'complete': '#A855F7',
      'completed': '#A855F7',
      'paused': '#F59E0B',
      'archived': '#6B7280',
    };

    // Build chart data
    return Object.entries(statusCounts).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      color: colors[name] || '#06B6D4',
    }));
  }, [projects]);

  // Calculate progress distribution
  const progressData = useMemo(() => {
    if (!projects || projects.length === 0) return [];

    const ranges = [
      { name: '0%', min: 0, max: 0, color: '#EF4444', value: 0 },
      { name: '1-25%', min: 1, max: 25, color: '#F59E0B', value: 0 },
      { name: '26-50%', min: 26, max: 50, color: '#EAB308', value: 0 },
      { name: '51-75%', min: 51, max: 75, color: '#84CC16', value: 0 },
      { name: '76-99%', min: 76, max: 99, color: '#22C55E', value: 0 },
      { name: '100%', min: 100, max: 100, color: '#10B981', value: 0 },
    ];

    projects.forEach(p => {
      const progress = p.progress_percentage || 0;
      for (const range of ranges) {
        if (progress >= range.min && progress <= range.max) {
          range.value++;
          break;
        }
      }
    });

    return ranges;
  }, [projects]);

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

  if (!projects || projects.length === 0) {
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
          <span className="text-sm text-white/60 font-medium">{projects.length} projects</span>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="grid grid-cols-2 gap-6">
          {/* Status Distribution - Pie Chart */}
          <div>
            <p className="text-xs text-white/50 mb-2 text-center">By Status</p>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                    labelLine={false}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(value, name) => [`${value} projects`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {statusData.map((item, i) => (
                <div key={i} className="flex items-center gap-1.5 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="text-white/60">{item.name}</span>
                  <span className="text-white/90 font-medium">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Progress Distribution - Bar Chart */}
          <div>
            <p className="text-xs text-white/50 mb-2 text-center">By Progress</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={progressData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="name"
                  stroke="#64748B"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  stroke="#64748B"
                  fontSize={10}
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
                  formatter={(value) => [`${value} projects`, 'Count']}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={36}>
                  {progressData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
