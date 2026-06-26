import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const submitUseCase = (description, structuredFields = {}) =>
  api.post('/use-case', { description, structured_fields: structuredFields });

export const submitClarification = (useCaseId, answers) =>
  api.post(`/use-case/${useCaseId}/clarify`, { answers });

export const getUseCases = () => api.get('/use-cases');
export const getDashboardStats = () => api.get('/dashboard-stats');
export const submitFeedback = (data) => api.post('/feedback', data);
export const submitChat = (useCaseId, messages) => api.post('/chat', { use_case_id: useCaseId, messages });
export const switchRecommendation = (useCaseId, model, cloud) =>
  api.post(`/use-case/${useCaseId}/switch`, { recommended_model: model, recommended_cloud: cloud });

export default api;
