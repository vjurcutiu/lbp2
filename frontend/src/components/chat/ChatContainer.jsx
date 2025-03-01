/**
 * ChatContainer Component
 *
 * This component serves as the main container for the chat interface.
 * It integrates the ChatHeader, ChatWindow, and ChatInput subcomponents to
 * display the chat header, conversation messages, and input field respectively.
 *
 * The component manages local state for the user input and handles sending
 * messages.
 */
import React, { useState } from 'react';
import ChatHeader from '../common/ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from '../common/ChatInput';
import { sendChatMessage } from '../../services';

const ChatContainer = ({ conversationId, messages, updateMessages }) => {
  const [input, setInput] = useState('');

  const handleSend = async (inputText) => {    
    console.log("Raw inputText received:", inputText);

    // Create a user message with a timestamp.
    const userMessage = { 
      sender: 'user', 
      message: inputText,
      created_at: new Date().toISOString()
    };

    // Update parent's messages.
    updateMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');

    try {
      // Call the API to send the message, including the conversation ID.
      const response = await sendChatMessage({ message: inputText, conversation_id: conversationId });
      console.log("API response:", response);
      // Map the API response to our message format.
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
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-100 dark:bg-gray-800">
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
