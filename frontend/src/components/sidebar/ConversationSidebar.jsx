import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
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
import { BsThreeDotsVertical } from "react-icons/bs";

const ContextMenu = ({ x, y, conversation, onEdit, onDelete, onClose }) => {
  return ReactDOM.createPortal(
    <div
      style={{ top: y, left: x }}
      className="fixed z-[10000] bg-white border border-gray-300 shadow-lg rounded"
      onClick={(e) => e.stopPropagation()}
    >
      <button
        className="flex items-center px-4 py-2 hover:bg-gray-100 w-full"
        onClick={() => { onEdit(conversation.id); onClose(); }}
      >
        <FaEdit className="mr-2" /> Edit
      </button>
      <button
        className="flex items-center px-4 py-2 hover:bg-gray-100 w-full"
        onClick={() => { onDelete(conversation.id); onClose(); }}
      >
        <MdDelete className="mr-2" /> Delete
      </button>
    </div>,
    document.body
  );
};

const ConversationSidebar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { conversations, activeConversationId } = useSelector((state) => state.conversations);
  console.log('conversation update in the sidebar', conversations);

  const [menuData, setMenuData] = useState({ open: false, conversation: null, x: 0, y: 0 });
  const buttonRef = useRef(null);

  const handleNewConversationClick = async () => {
    const newId = await dispatch(generateNewConversationThunk());
    navigate(`/conversation/${newId}`);
  };

  const handleConversationSelect = (conversationId) => {
    dispatch(selectConversation(conversationId));
  };

  const handleEditConversation = (conversationId) => {
    console.log("Edit conversation:", conversationId);
    // TODO: Add your edit logic here (e.g., open a modal or inline editor)
  };

  const handleDeleteConversation = (conversationId) => {
    console.log("Delete conversation:", conversationId);
    // TODO: Add your delete logic here (e.g., dispatch a delete action)
  };

  const openContextMenu = (e, conversation) => {
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    setMenuData({
      open: true,
      conversation,
      x: rect.right,
      y: rect.top,
    });
  };

  const closeContextMenu = () => {
    setMenuData({ open: false, conversation: null, x: 0, y: 0 });
  };

  return (
    <div 
      className="w-[250px] border-r border-gray-300 p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full relative" 
      onClick={closeContextMenu}
    >
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
            className={`relative flex items-center justify-between p-2 mb-1 cursor-pointer rounded ${
              conv.id === activeConversationId
                ? 'bg-gray-200 dark:bg-gray-700'
                : 'bg-transparent'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center flex-1">
              <Link
                to={`/conversation/${conv.id}`}
                className="flex-1"
                onClick={() => handleConversationSelect(conv.id)}
              >
                <span>{conv.title || `Conversation ${conv.id}`}</span>
              </Link>
              <div className="relative">
                <button 
                  ref={buttonRef}
                  className="flex justify-center items-center ml-2 px-2 py-1 rounded hover:bg-green-400"
                  onClick={(e) => openContextMenu(e, conv)}
                >
                  <BsThreeDotsVertical />
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      {menuData.open && menuData.conversation && (
        <ContextMenu 
          x={menuData.x} 
          y={menuData.y} 
          conversation={menuData.conversation}
          onEdit={handleEditConversation}
          onDelete={handleDeleteConversation}
          onClose={closeContextMenu}
        />
      )}
    </div>
  );
};

export default ConversationSidebar;
