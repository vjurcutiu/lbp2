// src/services/conversationApi.js
import apiClient from './apiClient';
import dayjs from 'dayjs';

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

export const getConversationMessages = async (conversationId) => {
  try {
    const response = await apiClient.get(`/conversation/${conversationId}/messages`);
    console.log("API response for conversation", conversationId, response);
    // Assuming response is like: { messages: [ { id, conversation_id, sender, message, created_at, ... }, ... ] }
    // Map over the messages and format the created_at field using Day.js
    const messages = response.messages.map(msg => ({
      ...msg,
      // Format the created_at date to a human-readable format, e.g., "3:45 PM"
      created_at: dayjs(msg.created_at).format('h:mm A')
    }));
    return messages;
  } catch (error) {
    console.error("Error fetching conversation messages:", error);
    throw error;
  }
};
