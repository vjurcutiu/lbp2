import React, { useState, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import { sendChatMessage } from '../../services';
import NewChat from './NewChat';

const ChatContainer = ({ conversationId, messages, updateMessages, onNewMessage }) => {
  const [input, setInput] = useState('');
  const [showChatWindow, setShowChatWindow] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);

  useEffect(() => {
    if (!conversationId) {
      setShowChatWindow(false);
    }
  }, [conversationId]);

  const handleSend = async (inputText) => {
    if (isWaiting) return; // Prevent sending if waiting for a response

    if (!showChatWindow) {
      setShowChatWindow(true);
    }

    console.log("Raw inputText received:", inputText);

    const userMessage = {
      sender: 'user',
      message: inputText,
      created_at: new Date().toISOString()
    };

    updateMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setIsWaiting(true);

    try {
      const response = await sendChatMessage({ message: inputText, conversation_id: conversationId });
      console.log("API response:", response);

      const aiReply = {
        sender: 'ai',
        message: response.ai_response || 'No response',
        created_at: response.ai_response?.created_at || new Date().toISOString()
      };

      updateMessages(prevMessages => [...prevMessages, aiReply]);
    } catch (error) {
      console.error('Error sending chat message:', error);

      updateMessages(prevMessages => [
        ...prevMessages,
        {
          sender: 'ai',
          message: 'Error processing your message. Please try again.',
          created_at: new Date().toISOString()
        }
      ]);
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

export default ChatContainer;
