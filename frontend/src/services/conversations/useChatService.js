import { useState, useCallback } from 'react';
import { sendChatMessage } from '../../services';

export const useChatService = ({ conversationId, onNewMessage, updateMessages }) => {
  const [isWaiting, setIsWaiting] = useState(false);

  const handleSend = useCallback(async (inputText) => {
    if (isWaiting) return;
    setIsWaiting(true);

    // Immediately add the user’s message.
    const userMessage = {
      sender: 'user',
      message: inputText,
      created_at: new Date().toISOString(),
    };
    updateMessages((prev) => [...prev, userMessage]);

    // Add a placeholder pending AI message.
    updateMessages((prev) => [
      ...prev,
      {
        sender: 'ai',
        pending: true,
        message: '',
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const response = await sendChatMessage({
        message: inputText,
        conversation_id: conversationId,
      });

      // If it’s a new conversation, let the parent know.
      if (!conversationId && response.new_conversation_id) {
        onNewMessage(response.new_conversation_id);
      }

      // Replace the pending message with the AI response.
      updateMessages((prev) => {
        const newMessages = [...prev];
        const pendingIndex = newMessages.findIndex((msg) => msg.pending);
        if (pendingIndex !== -1) {
          newMessages[pendingIndex] = {
            sender: 'ai',
            pending: false,
            message: response.ai_response || 'No response',
            created_at: response.ai_response?.created_at || new Date().toISOString(),
          };
        }
        return newMessages;
      });
    } catch (error) {
      console.error('Error sending message:', error);
      // Update the pending message with an error message.
      updateMessages((prev) => {
        const newMessages = [...prev];
        const pendingIndex = newMessages.findIndex((msg) => msg.pending);
        if (pendingIndex !== -1) {
          newMessages[pendingIndex] = {
            sender: 'ai',
            pending: false,
            message: 'Error processing your message. Please try again.',
            created_at: new Date().toISOString(),
          };
        }
        return newMessages;
      });
    } finally {
      setIsWaiting(false);
    }
  }, [isWaiting, conversationId, onNewMessage, updateMessages]);

  return { handleSend, isWaiting };
};
