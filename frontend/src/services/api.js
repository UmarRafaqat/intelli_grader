import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const checkHealth = async () => {
  const response = await api.get('/');
  return response.data;
};

// Ground Truth endpoints
export const autoConfigureQuestions = async (formData) => {
  const response = await api.post('/api/auto-configure', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const uploadGroundTruth = async (formData) => {
  const response = await api.post('/api/upload-ground-truth', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getExams = async () => {
  const response = await api.get('/api/exams');
  return response.data;
};

// Student Paper endpoints
export const uploadStudentPapers = async (formData) => {
  const response = await api.post('/api/upload-student-papers', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const gradePaper = async (submissionId) => {
  const response = await api.post(`/api/grade-paper/${submissionId}`);
  return response.data;
};

// Results endpoints
export const getResults = async (submissionIdOrStudentId) => {
  const response = await api.get(`/api/results/${submissionIdOrStudentId}`);
  return response.data;
};

// Teacher Review endpoints
export const getReview = async (submissionIdOrStudentId) => {
  const response = await api.get(`/api/review/${submissionIdOrStudentId}`);
  return response.data;
};

export const editGrade = async (submissionId, questionId, newScore, teacherComment) => {
  const formData = new FormData();
  formData.append('new_score', newScore);
  formData.append('teacher_comment', teacherComment);
  
  const response = await api.put(
    `/api/edit-grade/${submissionId}/${questionId}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );
  return response.data;
};

// Batch Processing endpoints
export const uploadBatchPapers = async (formData) => {
  const response = await api.post('/api/upload-batch-papers', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const gradeBatch = async (batchId) => {
  const response = await api.post(`/api/grade-batch/${batchId}`);
  return response.data;
};

export const getBatchStatus = async (batchId) => {
  const response = await api.get(`/api/batch-status/${batchId}`);
  return response.data;
};

export const exportBatchCSV = async (batchId) => {
  const response = await api.get(`/api/batch-results/${batchId}/csv`, {
    responseType: 'blob',
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `batch_${batchId}_results.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const getAllBatches = async () => {
  const response = await api.get('/api/batches');
  return response.data;
};

export default api;