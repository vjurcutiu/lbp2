// src/components/common/ConversationSidebar.jsx
import React from 'react';
import PropTypes from 'prop-types';
import FolderBrowseButton from './FolderBrowseButton';

const ConversationSidebar = ({ conversations, onSelect, activeConversationId, onFolderImport }) => {
  return (
    <div className="w-[250px] border-r border-gray-300 p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full">
      <div className="mb-4">
        <h2 className="mb-2 text-lg font-semibold">Conversations</h2>
        <FolderBrowseButton onFolderSelect={onFolderImport} buttonText="Import Files" />
      </div>
      <ul className="list-none p-0 m-0">
        {conversations.map((conv) => (
          <li
            key={conv.id}
            className={`p-2 mb-1 cursor-pointer rounded 
              ${conv.id === activeConversationId 
                ? 'bg-gray-200 dark:bg-gray-700' 
                : 'bg-transparent'}`}
            onClick={() => onSelect(conv.id)}
          >
            {conv.title || `Conversation ${conv.id}`}
          </li>
        ))}
      </ul>
    </div>
  );
};

ConversationSidebar.propTypes = {
  conversations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string,
    })
  ).isRequired,
  onSelect: PropTypes.func.isRequired,
  activeConversationId: PropTypes.number,
  onFolderImport: PropTypes.func.isRequired,
};

ConversationSidebar.defaultProps = {
  activeConversationId: null,
};

export default ConversationSidebar;
