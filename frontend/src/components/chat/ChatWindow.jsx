// src/components/chat/ChatWindow.jsx
import React from 'react';
import PropTypes from 'prop-types';

const ChatWindow = ({ messages }) => {
  return (
    <div style={styles.container}>
      {messages.map((msg, idx) => (
          <div 
            key={msg.id || `${msg.conversation_id}-${msg.created_at}-${idx}`} 
            style={msg.sender === 'user' ? styles.userMessage : styles.aiMessage}>
          <p style={styles.messageText}>{msg.message}</p>
          <small style={styles.timestamp}>
          {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : 'No timestamp'}
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
    height: '400px', // adjust height as needed
    backgroundColor: '#f2f2f2',
  },
  userMessage: {
    textAlign: 'right',
    backgroundColor: '#007bff',
    color: '#fff',
    padding: '8px 12px',
    borderRadius: '12px',
    marginBottom: '10px',
    maxWidth: '80%',
    alignSelf: 'flex-end',
  },
  aiMessage: {
    textAlign: 'left',
    backgroundColor: '#e0e0e0',
    color: '#000',
    padding: '8px 12px',
    borderRadius: '12px',
    marginBottom: '10px',
    maxWidth: '80%',
    alignSelf: 'flex-start',
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
