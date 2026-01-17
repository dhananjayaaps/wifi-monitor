import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = Cookies.get('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (email: string, password: string) =>
    apiClient.post('/auth/register', { email, password }),
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),
  me: () => apiClient.get('/auth/me'),
};

export const devicesAPI = {
  list: () => apiClient.get('/devices'),
  get: (id: number) => apiClient.get(`/devices/${id}`),
  getStats: (id: number, hours: number = 24) =>
    apiClient.get(`/devices/${id}/stats?hours=${hours}`),
};

export const agentsAPI = {
  list: () => apiClient.get('/agents'),
  register: (name: string) => apiClient.post('/agents/register', { name }),
};

export const alertsAPI = {
  list: () => apiClient.get('/alerts'),
  get: (id: number) => apiClient.get(`/alerts/${id}`),
  create: (data: any) => apiClient.post('/alerts', data),
  update: (id: number, data: any) => apiClient.put(`/alerts/${id}`, data),
};
