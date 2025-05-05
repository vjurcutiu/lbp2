import { useState, useCallback, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { sendChatMessage } from '../../services';
import { setNewConversationId } from '../storage/features/conversationSlice';
import socketService from '../../services/websocket/socketService.jsx';

export const useChatService = ({ conversationId, onNewMessage, updateMessages }) => {
  const [isWaiting, setIsWaiting] = useState(false);
  const dispatch = useDispatch();
  const aiMessageRef = useRef('');

  const handleSend = useCallback(
    async (inputText) => {
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

      // Streaming via websocket
      let socket = socketService.socket;
      if (!socket) {
        // Connect if not already connected (adjust URL/port as needed)
        socketService.connect('http://localhost:5000');
        socket = socketService.socket;
      }

      aiMessageRef.current = '';

      // Handler for streaming chunks
      const handleStream = (data) => {
        if (data && typeof data.chunk === 'string') {
          aiMessageRef.current += data.chunk;
          updateMessages((prev) => {
            const newMessages = [...prev];
            const pendingIndex = newMessages.findIndex((msg) => msg.pending);
            if (pendingIndex !== -1) {
              newMessages[pendingIndex] = {
                ...newMessages[pendingIndex],
                message: aiMessageRef.current,
              };
            }
            return newMessages;
          });
        }
        if (data && data.is_final) {
          // Mark as complete
          updateMessages((prev) => {
            const newMessages = [...prev];
            const pendingIndex = newMessages.findIndex((msg) => msg.pending);
            if (pendingIndex !== -1) {
              newMessages[pendingIndex] = {
                ...newMessages[pendingIndex],
                pending: false,
                message: aiMessageRef.current,
                created_at: new Date().toISOString(),
              };
            }
            return newMessages;
          });
          setIsWaiting(false);
          socketService.unsubscribeFromEvent('chat_stream');
        }
      };

      // Subscribe to streaming event
      socketService.subscribeToEvent('chat_stream', handleStream);

      // Emit chat message for streaming
      socketService.sendMessage('chat_message_stream', {
        message: inputText,
        conversation_id: conversationId,
      });

      // If it’s a new conversation, update the state with the new conversation ID (handled in backend if needed)
      // Optionally, you can listen for a 'new_conversation' event if you want to update the ID in real time

      // Fallback: If no response in X seconds, mark as error (optional)
      // You may want to add a timeout here for robustness
    },
    [isWaiting, conversationId, onNewMessage, updateMessages, dispatch]
  );

  return { handleSend, isWaiting };
};
