// ConversationSidebar.jsx

import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import FolderBrowseButton from './FolderBrowseButton';
import ContextMenu from './ContextMenu';
import RenameModal from './RenameModal';
import DeleteModal from './DeleteModal';
import UploadProgressModal from './UploadProgressModal';
import {
  generateNewConversationThunk,
  selectConversation
} from '../../services/storage/features/conversationSlice';
import { renameConversation, deleteConversation } from '../../services';
import { processFolder, cancelProcessFolder } from '../../services/folderApi';
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

  const [uploadProgress, setUploadProgress] = useState(0);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [currentSession, setCurrentSession] = useState({ id: null, es: null });

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

  const handleFolderSelect = async (folderPath) => {
    try {
      setShowProgressModal(true);
      setUploadProgress(0);

      // Start processing and get session info + promise
      const { sessionId, eventSource, resultPromise } = await processFolder(
        folderPath,
        ['.txt', '.pdf'],
        (progress) => setUploadProgress(progress)
      );

      // Keep for cancellation later
      setCurrentSession({ id: sessionId, es: eventSource });

      // Wait for processing to complete
      await resultPromise;

      // Once done, generate a new conversation and close modal
      dispatch(generateNewConversationThunk());
      setShowProgressModal(false);
      setCurrentSession({ id: null, es: null });
    } catch (err) {
      // If cancelled or error, log and simply close modal
      console.warn(err.message);
      setShowProgressModal(false);
      setCurrentSession({ id: null, es: null });
    }
  };

  const handleCancelUpload = async () => {
    // Close the SSE stream so we stop getting updates
    if (currentSession.es) {
      currentSession.es.close();
    }
    // Tell the server to cancel processing
    try {
      await cancelProcessFolder(currentSession.id);
    } catch (err) {
      console.error("Failed to cancel processing:", err);
    }
    // Hide the modal and reset state
    setShowProgressModal(false);
    setCurrentSession({ id: null, es: null });
  };

  return (
    <div
      className="w-[250px] border-r border-gray-300 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full relative"
      onClick={closeContextMenu}
    >
      <div className="h-15 flex items-center justify-center border-b border-gray-300">
        <FolderBrowseButton
          buttonText="Adauga Fisiere"
          onFolderSelect={handleFolderSelect}
          onError={(error) => console.error('File selection error:', error)}
        />
      </div>

      <div className="p-4">
        <h2 className="mb-2 text-sm font-semibold">Conversatii</h2>
        <button
          className="w-full mb-2 px-3 py-2 bg-blue-500 text-black rounded text-left"
          onClick={handleNewConversationClick}
        >
          <span className="text-sm">Conversatie Noua</span>
        </button>

        <ul className="list-none p-0 m-0">
          {conversations.map((conv) => (
            <li
              key={conv.id}
              className={`relative flex items-center justify-between mb-1 cursor-pointer rounded ${
                conv.id === activeConversationId ? 'bg-gray-200 dark:bg-gray-700' : 'bg-transparent'
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                className="group flex items-center px-3 py-2 rounded border border-transparent hover:bg-gray-200 justify-between"
                onClick={() => handleConversationSelect(conv.id)}
              >
                <Link
                  to={`/conversation/${conv.id}`}
                  className="text-sm"
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
      </div>

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

      {showProgressModal && (
        <UploadProgressModal
          progress={uploadProgress}
          onCancel={handleCancelUpload}
        />
      )}
    </div>
  );
};

export default ConversationSidebar;
