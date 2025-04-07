import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import FolderBrowseButton from './FolderBrowseButton';
import {
  clearActiveConversation,
  generateNewConversationThunk,
  selectConversation
} from '../../services/storage/features/conversationSlice';
import { FaEdit } from "react-icons/fa";
import { MdDelete } from "react-icons/md";

const ConversationSidebar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Subscribe to the Redux store for conversations data.
  const { conversations, activeConversationId } = useSelector((state) => state.conversations);
  console.log('conversation update in the sidebar', conversations);

  const handleNewConversationClick = async () => {
    const newId = await dispatch(generateNewConversationThunk());
    navigate(`/conversation/${newId}`);
  };

  const handleConversationSelect = (conversationId) => {
    dispatch(selectConversation(conversationId));
  };

  // New handler for editing a conversation
  const handleEditConversation = (conversationId) => {
    console.log("Edit conversation:", conversationId);
    // TODO: Add your edit logic here (e.g., open a modal or inline editor)
  };

  // New handler for deleting a conversation
  const handleDeleteConversation = (conversationId) => {
    console.log("Delete conversation:", conversationId);
    // TODO: Add your delete logic here (e.g., dispatch a delete action)
  };

  return (
    <div className="w-[250px] border-r border-gray-300 p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full">
      <div className="mb-4">
        <h2 className="mb-2 text-lg font-semibold">Conversations</h2>
        <button
          className="w-full mb-2 px-3 py-1 bg-blue-500 text-black rounded hover:bg-blue-600"
          onClick={handleNewConversationClick}
        >
          New Conversation
        </button>
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
            <div className="flex items-center flex-1">
              <Link
                to={`/conversation/${conv.id}`}
                className="flex-1"
                onClick={() => handleConversationSelect(conv.id)}
              >
                <span>{conv.title || `Conversation ${conv.id}`}</span>
              </Link>
              <button 
                className="flex justify-center items-center ml-2 px-2 py-1 rounded hover:bg-green-400"
                onClick={() => handleEditConversation(conv.id)}
              >
                <span>
                <FaEdit />
                </span>
              </button>
              <button 
                className="flex justify-center items-center ml-2 px-2 py-1 rounded hover:bg-red-400"
                onClick={() => handleDeleteConversation(conv.id)}
              >
                <span>
                <MdDelete/>
                </span>
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ConversationSidebar;
