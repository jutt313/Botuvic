import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService } from '@/services/projects';
import { useNotificationStore, notificationTypes } from '@/store/notificationStore';

export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsService.getAll,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useProject = (id) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsService.getById(id),
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((state) => state.addNotification);

  return useMutation({
    mutationFn: projectsService.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries(['projects']);
      
      // Add notification for project creation
      addNotification({
        type: notificationTypes.PROJECT_CREATED,
        title: 'Project Created',
        message: `Project "${data.name}" has been created successfully.`,
        details: {
          projectId: data.id,
          projectName: data.name,
          path: data.path,
          status: data.status,
        },
      });
    },
    onError: (error) => {
      // Add error notification
      addNotification({
        type: notificationTypes.ERROR_DETECTED,
        title: 'Project Creation Failed',
        message: error.message || 'Failed to create project. Please try again.',
        details: { error: error.message },
      });
    },
  });
};

export const useMetrics = () => {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: projectsService.getMetrics,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useActivity = (range = 'week') => {
  return useQuery({
    queryKey: ['activity', range],
    queryFn: () => projectsService.getActivity(range),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

