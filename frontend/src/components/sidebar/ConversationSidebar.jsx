import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import FolderBrowseButton from './FolderBrowseButton';

const ConversationSidebar = ({ conversations, activeConversationId }) => {
  console.log('Rendering ConversationSidebar. Active conversation:', activeConversationId);

  return (
    <div className="w-[250px] border-r border-gray-300 p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full">
      <div className="mb-4">
        <h2 className="mb-2 text-lg font-semibold">Conversations</h2>
        <Link to="/new">
          <button className="w-full mb-2 px-3 py-1 bg-blue-500 text-black rounded hover:bg-blue-600">
            New Conversation
          </button>
        </Link>
        <FolderBrowseButton buttonText="Import Files" />
      </div>
      <ul className="list-none p-0 m-0">
        {conversations.map((conv) => (
          <li
            key={conv.id}
            className={`flex items-center justify-between p-2 mb-1 cursor-pointer rounded ${
              conv.id === activeConversationId
                ? 'bg-gray-200 dark:bg-gray-700'
                : 'bg-transparent'
            }`}
          >
            <Link to={`/conversation/${conv.id}`} className="flex-1">
              <span>{conv.title || `Conversation ${conv.id}`}</span>
            </Link>
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
  activeConversationId: PropTypes.number,
};

ConversationSidebar.defaultProps = {
  activeConversationId: null,
};

export default ConversationSidebar;