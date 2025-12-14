import api from './api';

export const projectsService = {
  getAll: async () => {
    const response = await api.get('/projects/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/projects/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/projects/${id}`);
    return response.data;
  },

  getMetrics: async () => {
    const response = await api.get('/metrics');
    return response.data;
  },

  getActivity: async (range = 'week') => {
    const response = await api.get(`/metrics/activity?range=${range}`);
    return response.data;
  },
};

