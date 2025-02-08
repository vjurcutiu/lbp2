// src/services/folderApi.js
import apiClient from './apiClient';

export const processFolder = (payload) => {
  return apiClient.post('/files/process_folder', payload);
};
