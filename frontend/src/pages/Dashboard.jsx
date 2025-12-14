import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { MetricsGrid } from '@/components/metrics/MetricsGrid';
import { ProjectList } from '@/components/projects/ProjectList';
import { ActivityChart } from '@/components/charts/ActivityChart';

export const Dashboard = () => {
  const renderCountRef = React.useRef(0);

  React.useEffect(() => {
    renderCountRef.current += 1;
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/f4201013-abc5-489e-9ece-a98ac059c1d2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Dashboard.jsx:8',message:'Dashboard render',data:{renderCount:renderCountRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run5',hypothesisId:'I'})}).catch(()=>{});
    // #endregion
  }); // This will log every render but won't cause re-renders

  const handleNewProject = () => {
    // TODO: Open new project modal or navigate to project creation
    console.log('New project');
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container px-6 py-8 space-y-8">
        {/* Metrics */}
        <MetricsGrid />

        {/* Projects */}
        <ProjectList onNewProject={handleNewProject} />

        {/* Activity */}
        <ActivityChart />
      </main>
    </div>
  );
};

