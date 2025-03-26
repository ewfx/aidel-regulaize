import axios from 'axios';
import type { Entity, FileMetadata, TransactionStatistics } from '../types';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An error occurred';
    
    if (error.response) {
      // Server responded with error
      const detail = error.response.data.detail;
      if (typeof detail === 'string' && detail.includes('Neo4j')) {
        message = 'Graph database connection error. Please try again later.';
      } else if (detail.includes('MongoDB')) {
        message = 'Database connection error. Please try again later.';
      } else {
        message = detail || 'Server error';
      }
    } else if (error.request) {
      // No response received
      message = 'No response from server. Please check your connection.';
    }
    
    toast.error(message);
    return Promise.reject(error);
  }
);

export const searchEntities = async (query: string): Promise<Entity[]> => {
  try {
    const response = await api.get(`/entities?query=${encodeURIComponent(query)}`);
    return response.data;
  } catch (error) {
    console.error('Error searching entities:', error);
    throw error;
  }
};

export const getEntityById = async (id: string): Promise<Entity> => {
  try {
    const response = await api.get(`/entities/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error getting entity:', error);
    throw error;
  }
};

export const uploadFile = async (file: File): Promise<FileMetadata> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const getFileStatus = async (fileId: string): Promise<FileMetadata> => {
  try {
    const response = await api.get(`/files/${fileId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting file status:', error);
    throw error;
  }
};

export const getTransactionStatistics = async (): Promise<TransactionStatistics> => {
  try {
    const response = await api.get('/transactions/statistics');
    return response.data;
  } catch (error) {
    console.error('Error getting transaction statistics:', error);
    throw error;
  }
};

export const getRecentTransactions = async (limit: number = 5) => {
  try {
    const response = await api.get(`/transactions?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error getting recent transactions:', error);
    throw error;
  }
};