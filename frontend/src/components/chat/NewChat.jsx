import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

const NewChat = ({ messages, onNewMessage }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current && messages.length === 0) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
    if (onNewMessage && messages.length === 0) {
      onNewMessage();
    }
  }, [messages, onNewMessage]);

  // If there are messages, do not render the placeholder.
  if (messages.length > 0) {
    return null;
  }

  return (
    <div 
      ref={containerRef} 
      className="p-2.5 overflow-y-auto h-full w-full bg-gray-200 dark:bg-gray-700 flex flex-col"
    >
      <div className="flex-grow flex items-center justify-center">
        <p className="text-lg text-gray-600 dark:text-gray-300">
          This is the placeholder. No messages yet.
        </p>
      </div>
    </div>
  );
};

NewChat.propTypes = {
  messages: PropTypes.array.isRequired,
  onNewMessage: PropTypes.func,
};

export default NewChat;
