import { useState, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { sendChatMessage } from '../../services';
import { setNewConversationId } from '../storage/features/conversationSlice';

export const useChatService = ({ conversationId, onNewMessage, updateMessages }) => {
  const [isWaiting, setIsWaiting] = useState(false);
  const dispatch = useDispatch();

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

      console.log("Backend response:", response);


      // If it’s a new conversation, update the state with the new conversation ID.
      if (!conversationId && response.new_conversation_id) {
        dispatch(setNewConversationId(response.new_conversation_id));
        // Optionally, call the callback if needed.
        if (onNewMessage) {
          onNewMessage(response.new_conversation_id);
        }
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
  }, [isWaiting, conversationId, onNewMessage, updateMessages, dispatch]);

  return { handleSend, isWaiting };
};
