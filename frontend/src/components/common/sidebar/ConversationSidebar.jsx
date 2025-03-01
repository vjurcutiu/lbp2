import React, { useState } from 'react';
import PropTypes from 'prop-types';
import FolderBrowseButton from './FolderBrowseButton';

const ConversationSidebar = ({
  conversations,
  onSelect,
  activeConversationId,
  onFolderImport,
  onRenameConversation,
  onDeleteConversation,
  onNewConversation, // new prop
}) => {
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const openContextMenu = (conversation, event) => {
    event.stopPropagation();
    setSelectedConversation(conversation);
    setNewTitle(conversation.title || '');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedConversation(null);
    setNewTitle('');
  };

  const handleRename = () => {
    if (onRenameConversation && selectedConversation) {
      onRenameConversation(selectedConversation, newTitle);
    }
    closeModal();
  };

  const handleDelete = () => {
    if (onDeleteConversation && selectedConversation) {
      onDeleteConversation(selectedConversation);
    }
    closeModal();
  };

  return (
    <div className="w-[250px] border-r border-gray-300 p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full">
      <div className="mb-4">
        <h2 className="mb-2 text-lg font-semibold">Conversations</h2>
        {/* New Conversation Button */}
        <button
          className="w-full mb-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={onNewConversation}
        >
          New Conversation
        </button>
        <FolderBrowseButton onFolderSelect={onFolderImport} buttonText="Import Files" />
      </div>
      <ul className="list-none p-0 m-0">
        {conversations.map((conv) => (
          <li
            key={conv.id}
            className={`flex items-center justify-between p-2 mb-1 cursor-pointer rounded ${
              conv.id === activeConversationId ? 'bg-gray-200 dark:bg-gray-700' : 'bg-transparent'
            }`}
            onClick={() => onSelect(conv.id)}
          >
            <span>{conv.title || `Conversation ${conv.id}`}</span>
            <button
              className="ml-2 text-gray-500 hover:text-gray-700"
              onClick={(e) => openContextMenu(conv, e)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v.01M12 12v.01M12 18v.01" />
              </svg>
            </button>
          </li>
        ))}
      </ul>

      {isModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-4 rounded shadow-lg">
            <h3 className="text-lg font-medium mb-4">Options</h3>
            <div className="mb-4">
              <label htmlFor="newTitle" className="block mb-1">New Title</label>
              <input
                id="newTitle"
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="w-full border rounded px-2 py-1"
              />
            </div>
            <button
              className="block w-full text-left py-2 hover:bg-gray-100"
              onClick={handleRename}
            >
              Rename
            </button>
            <button
              className="block w-full text-left py-2 hover:bg-gray-100"
              onClick={handleDelete}
            >
              Delete
            </button>
            <button
              className="block w-full text-left py-2 mt-2 text-sm text-gray-500"
              onClick={closeModal}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
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
  onRenameConversation: PropTypes.func,
  onDeleteConversation: PropTypes.func,
  onNewConversation: PropTypes.func, // new prop type
};

ConversationSidebar.defaultProps = {
  activeConversationId: null,
  onRenameConversation: null,
  onDeleteConversation: null,
  onNewConversation: () => {}, // provide a default no-op
};

export default ConversationSidebar;
