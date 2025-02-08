// src/services/conversationApi.js
import apiClient from './apiClient';

export const getConversationIds = async () => {
  try {
    // Send a GET request to the conversation_ids route.
    const response = await apiClient.get('/conversation/conversation_ids');
    // Assuming the response data is like: { conversation_ids: [1, 2, 3, ...] }
    return response.conversation_ids;
  } catch (error) {
    console.error("Error fetching conversation ids:", error);
    throw error;
  }
};
