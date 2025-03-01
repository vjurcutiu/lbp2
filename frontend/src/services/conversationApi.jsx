import apiClient from './apiClient';
import dayjs from 'dayjs';

/**
 * Retrieves all conversations with their details.
 * Assumes the API returns a JSON object like:
 * { conversations: [ { id, title, created_at, ... }, ... ] }
 */
export const getConversations = async () => {
  try {
    const response = await apiClient.get('/conversation/list');
    // Optionally format the created_at timestamp for each conversation.
    const conversations = response.conversations.map(conv => ({
      ...conv,
      created_at: conv.created_at ? dayjs(conv.created_at).format('MMM D, YYYY h:mm A') : null,
    }));
    return conversations;
  } catch (error) {
    console.error("Error fetching conversations:", error);
    throw error;
  }
};

// The rest of your functions remain unchanged.
export const getConversationMessages = async (conversationId) => {
  try {
    const response = await apiClient.get(`/conversation/${conversationId}/messages`);
    const messages = response.messages.map(msg => ({
      ...msg,
      created_at: dayjs(msg.created_at).format('h:mm A')
    }));
    return messages;
  } catch (error) {
    console.error("Error fetching conversation messages:", error);
    throw error;
  }
};

export const deleteConversation = async (conversationId) => {
  try {
    const response = await apiClient.post('/conversation/delete', {
      conversation_id: conversationId,
    });
    return response.data;
  } catch (error) {
    console.error('Error deleting conversation:', error);
    throw error;
  }
};

export const renameConversation = async (conversationId, newTitle) => {
  try {
    const response = await apiClient.post('/conversation/rename', {
      conversation_id: conversationId,
      new_title: newTitle,
    });
    return response.data;
  } catch (error) {
    console.error('Error renaming conversation:', error);
    throw error;
  }
};
