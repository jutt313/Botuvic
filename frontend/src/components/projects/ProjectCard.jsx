import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ExternalLink, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

export const ProjectCard = ({ project }) => {
  const navigate = useNavigate();

  const statusColors = {
    active: 'bg-success',
    paused: 'bg-warning',
    complete: 'bg-secondary',
  };

  const status = project.status || 'active';
  const progress = project.progress_percentage || 0;
  const currentPhase = project.current_phase || 1;
  const totalPhases = project.total_phases || 3;
  const updatedAt = project.updated_at || project.created_at;

  return (
    <Card className="card-hover">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${statusColors[status] || statusColors.active}`} />
            <CardTitle className="text-xl">{project.name}</CardTitle>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/project/${project.id}`)}
          >
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {project.description && (
            <p className="text-sm text-text-muted">{project.description}</p>
          )}

          {/* Phase Info */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">
              Phase {currentPhase}/{totalPhases}
            </span>
            <span className="font-medium">{progress}%</span>
          </div>

          {/* Progress Bar */}
          <Progress value={progress} />

          {/* Last Active */}
          {updatedAt && (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Clock className="w-4 h-4" />
              <span>
                Last active {formatDistanceToNow(new Date(updatedAt), { addSuffix: true })}
              </span>
            </div>
          )}

          {/* Actions */}
          <Button
            className="w-full"
            onClick={() => navigate(`/project/${project.id}`)}
          >
            Open Project
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

