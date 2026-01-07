import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useProjects } from '@/hooks/useProjects';
import { projectsService } from '@/services/projects';
import { useQueryClient } from '@tanstack/react-query';
import { Trash2, Copy, Check, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useNotificationStore, notificationTypes } from '@/store/notificationStore';

export const ProjectsTable = () => {
  const { data: projects = [], isLoading } = useProjects();
  const queryClient = useQueryClient();
  const [copiedId, setCopiedId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const addNotification = useNotificationStore((state) => state.addNotification);

  const handleCopyId = async (id) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(id);
    try {
      await projectsService.delete(id);
      queryClient.invalidateQueries(['projects']);
      
      // Add notification
      addNotification({
        type: notificationTypes.PROJECT_DELETED,
        title: 'Project Deleted',
        message: `Project "${name}" has been deleted successfully.`,
        details: { projectId: id, projectName: name },
      });
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('Failed to delete project. Please try again.');
      
      // Add error notification
      addNotification({
        type: notificationTypes.ERROR_DETECTED,
        title: 'Delete Failed',
        message: `Failed to delete project "${name}". Please try again.`,
        details: { error: error.message, projectId: id },
      });
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'paused':
        return 'bg-yellow-500';
      case 'complete':
        return 'bg-blue-500';
      case 'archived':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'paused':
        return 'Paused';
      case 'complete':
        return 'Complete';
      case 'archived':
        return 'Archived';
      default:
        return status || 'Active';
    }
  };

  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white">Projects</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (projects.length === 0) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl text-white">Projects</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-white/60">
            <p>No projects found</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="text-xl text-white">Projects</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-sm font-semibold text-white/80">Name</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-white/80">Status</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-white/80">Progress</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-white/80">Created</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-white/80">Project ID</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-white/80">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr 
                  key={project.id} 
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-4 px-4">
                    <div className="font-medium text-white">{project.name}</div>
                    {project.description && (
                      <div className="text-sm text-white/60 mt-1 line-clamp-1">
                        {project.description}
                      </div>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(project.status)}`}>
                      <span className="w-2 h-2 rounded-full bg-white"></span>
                      {getStatusLabel(project.status)}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-purple-500 to-purple-600 transition-all"
                          style={{ width: `${project.progress_percentage || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-white/80 min-w-[3rem]">
                        {project.progress_percentage || 0}%
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-sm text-white/70">
                    {project.created_at ? (
                      <div>
                        <div>{new Date(project.created_at).toLocaleDateString()}</div>
                        <div className="text-xs text-white/50">
                          {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                        </div>
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <code className="text-xs text-white/60 font-mono bg-white/5 px-2 py-1 rounded">
                        {project.id.substring(0, 8)}...
                      </code>
                      <button
                        onClick={() => handleCopyId(project.id)}
                        className="p-1 hover:bg-white/10 rounded transition-colors"
                        title="Copy Project ID"
                      >
                        {copiedId === project.id ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4 text-white/60" />
                        )}
                      </button>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => window.open(`/project/${project.id}`, '_blank')}
                        className="text-white/70 hover:text-white"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(project.id, project.name)}
                        disabled={deletingId === project.id}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        {deletingId === project.id ? (
                          <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

