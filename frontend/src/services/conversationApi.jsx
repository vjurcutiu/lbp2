import apiClient from './apiClient';
import dayjs from 'dayjs';

/**
 * Retrieves all conversation IDs.
 * Assumes the API returns a JSON object like: { conversation_ids: [1, 2, 3, ...] }
 */
export const getConversationIds = async () => {
  try {
    const response = await apiClient.get('/conversation/conversation_ids');
    return response.conversation_ids;
  } catch (error) {
    console.error("Error fetching conversation ids:", error);
    throw error;
  }
};

/**
 * Retrieves messages for a given conversation.
 * Formats the created_at timestamp using dayjs.
 */
export const getConversationMessages = async (conversationId) => {
  try {
    const response = await apiClient.get(`/conversation/${conversationId}/messages`);
    // Format the created_at date to a human-readable format.
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

/**
 * Deletes a conversation by its ID.
 * Sends a POST request to the delete endpoint.
 */
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

/**
 * Renames a conversation by its ID.
 * Sends a POST request to the rename endpoint.
 */
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
