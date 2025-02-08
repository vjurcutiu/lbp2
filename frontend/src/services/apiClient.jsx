// src/services/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:5000/',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // Optional timeout
});

// Request interceptor (for example, to add an Authorization header)
apiClient.interceptors.request.use(
  (config) => {
    // config.headers.Authorization = `Bearer ${yourToken}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data, // Return data directly
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
