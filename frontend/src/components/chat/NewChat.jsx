import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';

const NewChat = ({ messages }) => {
  const containerRef = useRef(null);
  const navigate = useNavigate();

  // Get the active conversation id from Redux
  const activeConversationId = useSelector(
    (state) => state.conversations.activeConversationId
  );
  console.log("Current activeConversationId from Redux:", activeConversationId);

  // Navigate to the conversation page when a new conversation id is set
  useEffect(() => {
    console.log("useEffect triggered with activeConversationId:", activeConversationId);
    if (activeConversationId) {
      console.log("Navigating to /conversation/" + activeConversationId);
      navigate(`/conversation/${activeConversationId}`);
    }
  }, [activeConversationId, navigate]);

  // Additional UI logic...
  if (messages.length > 0) return null;

  return (
    <div
      ref={containerRef}
      className="p-2.5 overflow-y-auto h-full w-full bg-gray-100 dark:bg-gray-700 flex flex-col"
    >
      <div className="flex-grow flex items-center justify-center">
      </div>
    </div>
  );
};

NewChat.propTypes = {
  messages: PropTypes.array.isRequired,
};

export default NewChat;
