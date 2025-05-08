// services/apiClient.js
import axios from 'axios';
import { EventSourcePolyfill } from 'event-source-polyfill';


const apiClient = axios.create({
  // The default port here is just a fallback; this will be updated dynamically.
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Function to update the base URL with a new port.
export const updateApiClientBaseURL = (port) => {
  const finalPort = port || 5000; // default to 5000 if port is falsy
  apiClient.defaults.baseURL = `http://localhost:${finalPort}`;
};

// Optional: Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // config.headers.Authorization = `Bearer ${yourToken}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Optional: Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// SSE connection helper
export const createSSEConnection = (url, config = {}) => {
  const mergedConfig = {
    ...apiClient.defaults,
    ...config,
    headers: {
      ...apiClient.defaults.headers.common,
      ...config.headers,
    }
  };

  return new EventSourcePolyfill(`${mergedConfig.baseURL}${url}`, {
    headers: mergedConfig.headers,
    withCredentials: mergedConfig.withCredentials,
  });
};

export default apiClient;
