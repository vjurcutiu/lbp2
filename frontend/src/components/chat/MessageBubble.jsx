// src/components/common/MessageBubble.jsx
import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';

const MessageBubble = ({ sender, text, timestamp, style, className }) => {
  const isUser = sender === 'user';

  return (
    <div
      className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end mb-2 ${className}`}
      style={style}
    >
      <div className="mx-2">
        <img
          src={isUser ? '/path/to/user-avatar.png' : '/path/to/ai-avatar.png'}
          alt={`${sender} avatar`}
          className="w-8 h-8 rounded-full"
        />
      </div>
      <div
        className={`max-w-[70%] px-3 py-2 rounded-xl 
          ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-black dark:bg-gray-700 dark:text-white'}`}
      >
        <div>
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
        {timestamp && (
          <small className="text-xs opacity-70">
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
