import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProjectCard } from './ProjectCard';
import { useProjects } from '@/hooks/useProjects';
import { Plus } from 'lucide-react';

export const ProjectList = ({ onNewProject }) => {
  const { data: projects, isLoading, error } = useProjects();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">📁 Your Projects</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-surface rounded-lg p-6 animate-pulse">
                <div className="h-6 bg-white/10 rounded w-32 mb-4"></div>
                <div className="h-4 bg-white/10 rounded w-full mb-2"></div>
                <div className="h-2 bg-white/10 rounded w-full"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">📁 Your Projects</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-surface rounded-lg p-6 border border-error/50">
            <p className="text-error">Failed to load projects. Please try again later.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">📁 Your Projects</CardTitle>
          <Button onClick={onNewProject}>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-text-muted mb-4">No projects yet</p>
            <Button onClick={onNewProject}>
              Create Your First Project
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

