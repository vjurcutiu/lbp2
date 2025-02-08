// src/services/api.js
import axios from 'axios';

// Create an axios instance with your API base URL and default settings
const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api', // Adjust the base URL as needed
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // Optional timeout
});

// Add request interceptors if needed (for authentication, logging, etc.)
apiClient.interceptors.request.use(
  (config) => {
    // For example, add an Authorization header here if you have a token
    // config.headers.Authorization = `Bearer ${yourToken}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptors if needed
apiClient.interceptors.response.use(
  (response) => response.data, // Return data directly
  (error) => {
    // Handle errors globally
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Export functions for your API endpoints
export const sendChatMessage = (payload) => {
  return apiClient.post('/chat', payload);
};

export const processFolder = (payload) => {
  return apiClient.post('/files/process_folder', payload);
};

// Add more functions for other endpoints as needed
