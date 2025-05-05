// src/components/common/ChatHeader.jsx
import React from 'react';
import PropTypes from 'prop-types';
import DarkModeToggle from '../darkMode/DarkModeToggle';
import { useSelector } from 'react-redux';


const ChatHeader = ({ onBack, className }) => {
  const activeConversationId = useSelector(
    (state) => state.conversations.activeConversationId
  );
  const conversations = useSelector((state) => state.conversations.conversations);

  // Find the active conversation if it exists
  const conversation = conversations.find(
    (conv) => conv.id === activeConversationId
  );

  // If no active conversation, default to "New Conversation"
  // Otherwise, if conversation exists, use its title, defaulting to "Conversation {ID}" if no title is set.
  const title =
    !activeConversationId || !conversation
      ? 'Cautare Noua'
      : conversation.title || `Conversatia ${activeConversationId}`;

  return (
    <div className={`flex items-center justify-between p-3.5 bg-gray-200 dark:bg-gray-700 w-full shadow-sm ${className}`}>
      <div className="flex items-center">
        {onBack && (
          <button onClick={onBack} className="mr-2.5">
            Back
          </button>
        )}
        <h2 className="text-2xl font-bold flex items-center gap-2">
        {title}
        </h2>
      </div>
    </div>
  );
};

ChatHeader.propTypes = {
  onBack: PropTypes.func,
  className: PropTypes.string,
};

ChatHeader.defaultProps = {
  onBack: null,
  className: '',
};

export default ChatHeader;
