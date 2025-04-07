import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import FolderBrowseButton from './FolderBrowseButton';
import ContextMenu from './ContextMenu';
import RenameModal from './RenameModal';
import DeleteModal from './DeleteModal';
import {
  generateNewConversationThunk,
  selectConversation
} from '../../services/storage/features/conversationSlice';
import { renameConversation, deleteConversation } from '../../services';
import { BsThreeDotsVertical } from 'react-icons/bs';

const ConversationSidebar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { conversations, activeConversationId } = useSelector((state) => state.conversations);

  const [menuData, setMenuData] = useState({ open: false, conversation: null, x: 0, y: 0 });
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renameConversationId, setRenameConversationId] = useState(null);
  const [newTitle, setNewTitle] = useState("");
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

  const handleDeleteConversation = (conversationId) => {
    setDeleteConversationId(conversationId);
    setIsDeleteModalOpen(true);
  };

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
        <h2 className="mb-2 text-sm font-semibold">Conversations</h2>
        <button
          className="w-full mb-2 px-3 py-1 bg-blue-500 text-black rounded hover:bg-blue-600"
          onClick={handleNewConversationClick}
        >
          <span className='text-sm'>New Conversation</span>
        </button>
        <FolderBrowseButton buttonText="Import Files" />
      </div>

      <ul className="list-none p-0 m-0">
        {conversations.map((conv) => (
          <li
          key={conv.id}
          className={`relative flex items-center justify-between p-2 mb-1 cursor-pointer rounded ${
            conv.id === activeConversationId ? 'bg-gray-200 dark:bg-gray-700' : 'bg-transparent'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Add the "group" class to enable group-hover targeting */}
          <div className="group flex items-center flex-1 rounded border border-transparent hover:bg-gray-200">
            <Link
              to={`/conversation/${conv.id}`}
              className="flex-1 text-sm"
              onClick={() => handleConversationSelect(conv.id)}
            >
              <span>{conv.title || `Conversation ${conv.id}`}</span>
            </Link>
            <div className="relative">
              <button 
                ref={buttonRef}
                className="cursor-pointer flex justify-center items-center ml-2 px-1 py-1 rounded-full bg-transparent border-0 hover:!bg-gray-400 group-hover:!bg-transparent"
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
        <RenameModal 
          newTitle={newTitle}
          setNewTitle={setNewTitle}
          onClose={closeRenameModal}
          onSave={handleRenameSubmit}
        />
      )}

      {isDeleteModalOpen && (
        <DeleteModal 
          onClose={closeDeleteModal}
          onConfirm={confirmDeleteConversation}
        />
      )}
    </div>
  );
};

export default ConversationSidebar;
