import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chat = async (message, useRAG, useMemory) => {
  return apiClient.post('/chat', {
    message,
    use_rag: useRAG,
    include_memory: useMemory,
  }, {
    responseType: 'stream',
  });
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/upload-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const listDocuments = () => apiClient.get('/documents');

export const deleteDocument = (filename) => apiClient.post(`/delete-document/${filename}`);

export const transcribeAudio = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/voice/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const saveMemory = (title, content, type) =>
  apiClient.post('/memory', { title, content, memory_type: type });

export const getMemory = (type) => apiClient.get(`/memory/${type}`);

export const listModels = () => apiClient.get('/models');

export const getHistory = () => apiClient.get('/history');

export const clearHistory = () => apiClient.post('/clear-history');

export const listTasks = (status) =>
  apiClient.get('/tasks', { params: status ? { status } : {} });

export const createTask = (title, description = '', priority = 'medium', scheduled = null) =>
  apiClient.post('/tasks', { title, description, priority, scheduled });

export const updateTask = (id, fields) => apiClient.patch(`/tasks/${id}`, fields);

export const deleteTask = (id) => apiClient.delete(`/tasks/${id}`);

export const runAgent = (taskId = null, goal = null) =>
  apiClient.post('/agent/run', { task_id: taskId, goal }, { responseType: 'stream' });

export const suggestNextSteps = () => apiClient.post('/agent/next');
