/**
 * ChatContainer Component
 *
 * This component serves as the main container for the chat interface.
 * It integrates the ChatHeader, ChatWindow, and ChatInput subcomponents to
 * display the chat header, conversation messages, and input field respectively.
 *
 * The component manages local state for the user input and handles sending
 * messages. Upon sending a message, it:
 *   - Creates a user message with a timestamp.
 *   - Updates the conversation state with the new message.
 *   - Calls an API to process the message and receive an AI response.
 *   - Updates the conversation state with the AI's reply or an error message if the API call fails.
 *
 * Props:
 *   - conversationId: Identifier for the current chat conversation.
 *   - messages: An array of current chat messages.
 *   - updateMessages: A function to update the conversation messages.
 */
// src/components/chat/ChatContainer.jsx
import { React, useState } from 'react';
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
      // Map the API response to our message format. Adjust the keys based on your API.
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
    <div style={styles.container}>
      <ChatHeader title="Chat App" />
      <ChatWindow messages={messages} />
      <ChatInput         
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={handleSend} />
    </div>
  );
};

const styles = {
  container: {
    width: '100%', // Fill parent's width
    height: '100%', // Fill parent's height
    display: 'flex',
    flexDirection: 'column', // Arrange children vertically
    backgroundColor: '#f8f8f8'
  },
  header: {
    flex: '0 0 15%', // 10% height
  },
  chatWindow: {
    flex: '0 0 65%', // 80% height
    overflowY: 'auto', // Enable scrolling if content exceeds available height
  },
  input: {
    flex: '0 0 20%', // 10% height
  },
};

export default ChatContainer;
