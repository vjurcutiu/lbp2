// src/services/chatApi.js
import apiClient from './apiClient';

export const sendChatMessage = (payload) => {
  console.log("Sending payload:", payload);
  return apiClient.post('/conversation/chat', payload);
};
