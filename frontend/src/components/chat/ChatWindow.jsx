/**
 * ChatWindow Component
 *
 * This component is responsible for displaying the conversation messages
 * in a scrollable window.
 */
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import ChatMarkdownRenderer from './ChatMarkdownRenderer';
import './styles/ChatWindow.css'

const ChatWindow = ({ messages }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto p-2.5 w-full bg-gray-200 dark:bg-gray-700 flex flex-col"
    >
      {messages.map((msg, idx) => (
        <div
          key={msg.id || `${msg.conversation_id}-${msg.created_at}-${idx}`}
          className={
            msg.sender === 'user'
              ? 'self-end max-w-[60%] bg-gray-300 text-black px-3 py-2 rounded-xl mb-2.5'
              : 'self-start text-black dark:text-white px-3 py-2 rounded-xl mb-2.5'
          }
        >
          <div className="m-0">
            {msg.pending ? (
              <div className="flex justify-center my-2">
                <div className="spinner"> </div>
              </div>
            ) : msg.sender === 'ai' ? (
              <ChatMarkdownRenderer content={msg.message} />
            ) : (
              <div>{msg.message}</div>
            )}
          </div>
           {/*
          <small className="text-xs opacity-60">
            {msg.created_at && !isNaN(new Date(msg.created_at).getTime())
              ? new Date(msg.created_at).toLocaleTimeString()
              : msg.created_at || 'No timestamp'}
          </small>
          */}
        </div>
      ))}
    </div>
  );
};

ChatWindow.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      conversation_id: PropTypes.number.isRequired,
      sender: PropTypes.string.isRequired,
      message: PropTypes.string.isRequired,
      created_at: PropTypes.string.isRequired,
      meta_data: PropTypes.any,
      pending: PropTypes.bool,
    })
  ).isRequired,
};

export default ChatWindow;
