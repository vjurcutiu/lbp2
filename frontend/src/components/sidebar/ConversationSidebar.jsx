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
import { renameConversation, deleteConversation } from '../../services';

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

  const [menuData, setMenuData] = useState({ open: false, conversation: null, x: 0, y: 0 });
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renameConversationId, setRenameConversationId] = useState(null);
  const [newTitle, setNewTitle] = useState("");

  // New state for delete confirmation modal
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConversationId, setDeleteConversationId] = useState(null);

  const buttonRef = useRef(null);

  const handleNewConversationClick = async () => {
    const newId = await dispatch(generateNewConversationThunk());
    navigate(`/conversation/${newId}`);
  };

  const handleConversationSelect = (conversationId) => {
    dispatch(selectConversation(conversationId));
  };

  const handleEditConversation = (conversationId) => {
    const conv = conversations.find(c => c.id === conversationId);
    setRenameConversationId(conversationId);
    setNewTitle(conv?.title || "");
    setIsRenameModalOpen(true);
  };

  // Modified onDelete handler to open delete confirmation modal
  const handleDeleteConversation = (conversationId) => {
    setDeleteConversationId(conversationId);
    setIsDeleteModalOpen(true);
  };

  // Confirm deletion by calling deleteConversation and then closing the modal
  const confirmDeleteConversation = () => {
    if (deleteConversationId) {
      deleteConversation(deleteConversationId);
      setIsDeleteModalOpen(false);
      setDeleteConversationId(null);
    }
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setDeleteConversationId(null);
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

  const closeRenameModal = () => {
    setIsRenameModalOpen(false);
    setRenameConversationId(null);
    setNewTitle("");
  };

  const handleRenameSubmit = async () => {
    if (!renameConversationId || !newTitle) return;
    try {
      await renameConversation(renameConversationId, newTitle);
      closeRenameModal();
    } catch (error) {
      console.error("Error renaming conversation", error);
    }
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

      {isRenameModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white p-4 rounded shadow-lg w-[300px]">
            <h3 className="mb-2 text-lg font-semibold">Rename Conversation</h3>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="border border-gray-300 p-2 mb-4 w-full"
            />
            <div className="flex justify-end">
              <button className="px-3 py-1 mr-2 bg-gray-300 rounded" onClick={closeRenameModal}>
                Cancel
              </button>
              <button className="px-3 py-1 bg-blue-500 text-white rounded" onClick={handleRenameSubmit}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {isDeleteModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white p-4 rounded shadow-lg w-[300px]">
            <h3 className="mb-2 text-lg font-semibold">Delete Conversation</h3>
            <p className="mb-4">Are you sure you want to delete this conversation?</p>
            <div className="flex justify-end">
              <button className="px-3 py-1 mr-2 bg-gray-300 rounded" onClick={closeDeleteModal}>
                Cancel
              </button>
              <button className="px-3 py-1 bg-red-500 text-white rounded" onClick={confirmDeleteConversation}>
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConversationSidebar;
