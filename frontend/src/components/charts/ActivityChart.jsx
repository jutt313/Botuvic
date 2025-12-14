import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useActivity } from '@/hooks/useProjects';

export const ActivityChart = () => {
  const [timeRange, setTimeRange] = useState('week');
  const { data: activity, isLoading, error } = useActivity(timeRange);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">📈 Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">📈 Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-surface rounded-lg p-6 border border-error/50">
            <p className="text-error">Failed to load activity data. Please try again later.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!activity || activity.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">📈 Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-text-muted">
            <p>No activity data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">📈 Activity</CardTitle>
          
          {/* Time Range Selector */}
          <div className="flex gap-2">
            <button
              onClick={() => setTimeRange('week')}
              className={`px-3 py-1 rounded text-sm transition-all duration-200 ${
                timeRange === 'week'
                  ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg'
                  : 'bg-background text-text-muted hover:text-text hover:bg-surface'
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setTimeRange('month')}
              className={`px-3 py-1 rounded text-sm transition-all duration-200 ${
                timeRange === 'month'
                  ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg'
                  : 'bg-background text-text-muted hover:text-text hover:bg-surface'
              }`}
            >
              Month
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={activity}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="date" 
              stroke="#64748B"
              style={{ fontSize: 12 }}
            />
            <YAxis 
              stroke="#64748B"
              style={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E293B',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="commits" 
              stroke="#A855F7" 
              strokeWidth={2}
              dot={{ fill: '#A855F7', r: 4 }}
              name="Commits"
            />
            <Line 
              type="monotone" 
              dataKey="tasks" 
              stroke="#06B6D4" 
              strokeWidth={2}
              dot={{ fill: '#06B6D4', r: 4 }}
              name="Tasks"
            />
            <Line 
              type="monotone" 
              dataKey="aiCalls" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={{ fill: '#10B981', r: 4 }}
              name="AI Calls"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

