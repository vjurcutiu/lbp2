// src/components/chat/ChatContainer.jsx
import React from 'react';
import ChatHeader from '../common/ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from '../common/ChatInput';
import { sendChatMessage } from '../../services';

const ChatContainer = ({ conversationId, messages, updateMessages }) => {
  const handleSend = async (inputText) => {
    const trimmedInput = inputText.trim();
    if (!trimmedInput) return;

    // Create a user message with a timestamp.
    const userMessage = { 
      sender: 'user', 
      text: trimmedInput,
      created_at: new Date().toISOString()
    };

    // Update parent's messages.
    updateMessages(prevMessages => [...prevMessages, userMessage]);

    try {
      // Call the API to send the message, including the conversation ID.
      const response = await sendChatMessage({ message: trimmedInput, conversation_id: conversationId });
      console.log("API response:", response);
      // Map the API response to our message format. Adjust the keys based on your API.
      const aiReply = { 
        sender: 'ai', 
        text: response.ai_response?.message || 'No response',
        created_at: response.ai_response?.created_at || new Date().toISOString()
      };
      updateMessages(prevMessages => [...prevMessages, aiReply]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      updateMessages(prevMessages => [
        ...prevMessages,
        { 
          sender: 'ai', 
          text: 'Error processing your message. Please try again.',
          created_at: new Date().toISOString()
        }
      ]);
    }
  };

  return (
    <div>
      <ChatHeader title="Chat App" />
      <ChatWindow messages={messages} />
      <ChatInput onSend={handleSend} />
    </div>
  );
};

export default ChatContainer;
