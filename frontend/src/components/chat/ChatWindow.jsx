// src/components/common/ChatWindow.jsx
import React from 'react';
import PropTypes from 'prop-types';

const ChatWindow = ({ messages }) => {
  return (
    <div style={styles.container}>
      {messages.map((msg, index) => (
        <div key={index} style={msg.sender === 'user' ? styles.userMessage : styles.aiMessage}>
          {msg.text}
        </div>
      ))}
    </div>
  );
};

const styles = {
  container: {
    flex: 1,
    overflowY: 'auto',
    padding: '10px',
    backgroundColor: '#f2f2f2',
  },
  userMessage: {
    textAlign: 'right',
    padding: '5px',
    margin: '5px 0',
    backgroundColor: '#007bff',
    color: '#fff',
    borderRadius: '10px',
  },
  aiMessage: {
    textAlign: 'left',
    padding: '5px',
    margin: '5px 0',
    backgroundColor: '#e0e0e0',
    color: '#000',
    borderRadius: '10px',
  },
};

ChatWindow.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      sender: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
    })
  ).isRequired,
};

export default ChatWindow;
