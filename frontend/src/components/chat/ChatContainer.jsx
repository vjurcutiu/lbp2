// src/components/chat/ChatContainer.jsx
import React, { useState } from 'react';
import ChatHeader from '../common/ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from '../common/ChatInput';
import { sendChatMessage } from '../../services';

const ChatContainer = () => {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Welcome to the chat! How can I help you today?' },
  ]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput) return;

    const userMessage = { sender: 'user', text: trimmedInput };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');

    try {
      // Call the API to send the chat message
      const response = await sendChatMessage({ message: trimmedInput });
      console.log(response)
      // Assume the response contains an object like { ai_response: { text: '...' } }
      const aiReply = { sender: 'ai', text: response.ai_response || 'No response' };
      setMessages((prevMessages) => [...prevMessages, aiReply]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: 'Error processing your message. Please try again.' },
      ]);
    }
  };

  return (
    <div>
      <ChatHeader title="Chat App" />
      <ChatWindow messages={messages} />
      <ChatInput
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={handleSend}
      />
    </div>
  );
};

export default ChatContainer;
