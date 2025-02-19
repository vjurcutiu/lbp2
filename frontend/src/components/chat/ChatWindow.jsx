/**
 * ChatWindow Component
 *
 * This component is responsible for displaying the conversation messages
 * in a scrollable window. It maps through the provided messages array and renders
 * each message with styling based on the sender type (user or AI). Each message
 * includes the message text and a timestamp indicating when it was created.
 *
 * The component also leverages PropTypes to enforce the structure of the message
 * objects passed in via the "messages" prop.
 */

// src/components/chat/ChatWindow.jsx
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

const ChatWindow = ({ messages }) => {
  const containerRef = useRef(null);

  // Scroll to the bottom every time messages update
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);
  console.log(messages)

  return (
    <div ref={containerRef} style={styles.container}>
      {messages.map((msg, idx) => (
        <div 
          key={msg.id || `${msg.conversation_id}-${msg.created_at}-${idx}`} 
          style={msg.sender === 'user' ? styles.userMessage : styles.aiMessage}>
          <p style={styles.messageText}>{msg.message}</p>
          <small style={styles.timestamp}>
            {msg.created_at && !isNaN(new Date(msg.created_at).getTime())
              ? new Date(msg.created_at).toLocaleTimeString()
              : msg.created_at || 'No timestamp'}
        </small>
        </div>
      ))}
    </div>
  );
};

const styles = {
  container: {
    padding: '10px',
    overflowY: 'auto',
    height: '100%', // adjust height as needed
    width: '100%',
    backgroundColor: '#f2f2f2',
    display: 'flex',
    flexDirection: 'column',
  },
  userMessage: {
    textAlign: 'left',
    backgroundColor: '#007bff',
    color: '#fff',
    padding: '8px 12px',
    borderRadius: '12px',
    marginBottom: '10px',
    maxWidth: '60%',
    alignSelf: 'flex-end',
    wordWrap: 'break-word',
  },
  aiMessage: {
    textAlign: 'left',
    backgroundColor: '#e0e0e0',
    color: '#000',
    padding: '8px 12px',
    borderRadius: '12px',
    marginBottom: '10px',
    maxWidth: '60%',
    alignSelf: 'flex-start',
    wordWrap: 'break-word',
  },
  messageText: {
    margin: 0,
  },
  timestamp: {
    fontSize: '10px',
    opacity: 0.6,
  },
};

ChatWindow.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      conversation_id: PropTypes.number.isRequired,
      sender: PropTypes.string.isRequired,
      message: PropTypes.string.isRequired,
      created_at: PropTypes.string.isRequired,
      meta_data: PropTypes.any,
    })
  ).isRequired,
};

export default ChatWindow;

