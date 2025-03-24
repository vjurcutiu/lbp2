import React, { useState, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import { sendChatMessage } from '../../services/';
import NewChat from './NewChat';

const ChatMetaContainer = ({ conversationId, messages, updateMessages, onNewMessage }) => {
  const [input, setInput] = useState('');
  const [showChatWindow, setShowChatWindow] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);

  useEffect(() => {
    if (!conversationId) setShowChatWindow(false);
  }, [conversationId]);

  const handleSend = async (inputText) => {
    if (isWaiting) return;
    if (!showChatWindow) setShowChatWindow(true);

    const userMessage = {
      sender: 'user',
      message: inputText,
      created_at: new Date().toISOString(),
    };

    console.log('Sending user message:', userMessage);
    updateMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsWaiting(true);

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

      console.log('Response from sendChatMessage:', response);

      if (!conversationId && response.new_conversation_id) {
        onNewMessage(response.new_conversation_id);
      }

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
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-100 dark:bg-gray-800">
      <ChatHeader title="Chat App" />
      {conversationId ? (
        <ChatWindow messages={messages} />
      ) : (
        <NewChat messages={messages} onNewMessage={onNewMessage} />
      )}
      <ChatInput
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={handleSend}
        disabled={isWaiting}
      />
    </div>
  );
};

export default ChatMetaContainer;
