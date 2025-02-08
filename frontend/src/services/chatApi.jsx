// src/services/chatApi.js
import apiClient from './apiClient';

export const sendChatMessage = (payload) => {
  return apiClient.post('/conversation/chat', payload);
};
