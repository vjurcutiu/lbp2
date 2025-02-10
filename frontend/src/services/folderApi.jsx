// src/services/folderApi.js
import apiClient from './apiClient';

//FIXME: 
export const processFolder = (payload) => {
  return apiClient.post('/files/test_process_folder', payload);
};
