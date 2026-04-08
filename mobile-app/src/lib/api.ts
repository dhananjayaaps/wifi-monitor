import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// For Android emulator use: http://10.0.2.2:5000/api/v1
// For iOS simulator or physical device on LAN, use your machine's IP, e.g. http://192.168.1.x:5000/api/v1
const API_BASE_URL = 'http://localhost:5000/api/v1';

// Callback registered by AuthContext so a 401 triggers a full sign-out
let _onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: () => void): void {
  _onUnauthorized = handler;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem('access_token');
      // Notify AuthContext so it clears token state and redirects to login
      _onUnauthorized?.();
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
  getStats: (id: number, hours: number = 24, bucketMinutes?: number) => {
    const params = new URLSearchParams({ hours: String(hours) });
    if (bucketMinutes && bucketMinutes > 0) {
      params.set('bucket_minutes', String(bucketMinutes));
    }
    return apiClient.get(`/devices/${id}/stats?${params.toString()}`);
  },
  setCap: (id: number, data_cap: number | null) =>
    apiClient.put(`/devices/${id}/cap`, { data_cap }),
  delete: (id: number) => apiClient.delete(`/devices/${id}`),
  clearStats: (id: number) => apiClient.delete(`/devices/${id}/stats`),
};

export const agentsAPI = {
  list: () => apiClient.get('/agents'),
  register: (name: string) => apiClient.post('/agents/register', { name }),
};

export const alertsAPI = {
  list: () => apiClient.get('/alerts'),
  history: (params?: { hours?: number; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.hours != null) query.set('hours', String(params.hours));
    if (params?.limit != null) query.set('limit', String(params.limit));
    if (params?.offset != null) query.set('offset', String(params.offset));
    const suffix = query.toString();
    return apiClient.get(`/alerts/history${suffix ? `?${suffix}` : ''}`);
  },
  clearHistory: () => apiClient.delete('/alerts/history'),
};

export const settingsAPI = {
  get: () => apiClient.get('/system/settings'),
  update: (default_device_cap: number | null) =>
    apiClient.put('/system/settings', { default_device_cap }),
};
