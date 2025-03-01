// src/components/common/MessageBubble.jsx
import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';

const MessageBubble = ({ sender, text, timestamp, style, className }) => {
  const isUser = sender === 'user';
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-end',
        marginBottom: '10px',
        ...style,
      }}
    >
      {/* Optionally include an avatar */}
      <div style={{ margin: '0 8px' }}>
        {/* Placeholder for avatar */}
        <img
          src={isUser ? '/path/to/user-avatar.png' : '/path/to/ai-avatar.png'}
          alt={`${sender} avatar`}
          style={{ width: '32px', height: '32px', borderRadius: '50%' }}
        />
      </div>
      <div
        style={{
          maxWidth: '70%',
          padding: '8px 12px',
          borderRadius: '10px',
          backgroundColor: isUser ? '#007bff' : '#f1f0f0',
          color: isUser ? '#fff' : '#000',
        }}
      >
        <div style={{ margin: 0 }}>
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
        {timestamp && (
          <small style={{ fontSize: '10px', opacity: 0.7 }}>
            {timestamp}
          </small>
        )}
      </div>
    </div>
  );
};

MessageBubble.propTypes = {
  sender: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
  timestamp: PropTypes.string,
  style: PropTypes.object,
  className: PropTypes.string,
};

MessageBubble.defaultProps = {
  timestamp: null,
  style: {},
  className: '',
};

export default MessageBubble;
