import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import FolderBrowseButton from './FolderBrowseButton';
import ContextMenu from './ContextMenu';
import RenameModal from './RenameModal';
import DeleteModal from './DeleteModal';
import UploadProgressModal from '../../features/uploadTracking/UploadProgressModal';
import KeyModal from './KeyModal';
import { BsThreeDotsVertical } from 'react-icons/bs';
import { FaSearch, FaKey } from 'react-icons/fa';
import {
  generateNewConversationThunk,
  selectConversation
} from '../../services/storage/features/conversationSlice';
import { renameConversation, deleteConversation } from '../../services';
import { processFolder, cancelProcessFolder } from '../../services/folderApi';
import { uploadTrackingService } from '../../singletons';

const ConversationSidebar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { conversations, activeConversationId } = useSelector((state) => state.conversations);

  const [menuData, setMenuData] = useState({ open: false, conversation: null, x: 0, y: 0 });
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renameConversationId, setRenameConversationId] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConversationId, setDeleteConversationId] = useState(null);

  const [uploadProgress, setUploadProgress] = useState(0);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);

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
    setNewTitle(conv?.title || '');
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
    setNewTitle('');
  };

  const handleRenameSubmit = async () => {
    if (!renameConversationId || !newTitle) return;
    try {
      await renameConversation(renameConversationId, newTitle);
      closeRenameModal();
    } catch (error) {
      console.error('Error renaming conversation', error);
    }
  };

  const handleFolderSelect = async (folderPath) => {
    try {
      setShowProgressModal(true);
      setUploadProgress(0);

      // 1. Kick off the job, get sessionId (no singleton call in API)
      const sessionId = await processFolder(
        folderPath,
        ['.txt', '.pdf']
      );

      setCurrentSessionId(sessionId);

      // 2. Connect the singleton to WS
      uploadTrackingService.connect(sessionId);

      // The rest: wait for upload to complete via Redux state & modal
      // UI can react to uploadTrackingSlice changes (as before)

    } catch (err) {
      console.warn(err.message);
      setShowProgressModal(false);
      setCurrentSessionId(null);
    }
  };

  const handleCancelUpload = async () => {
    try {
      await cancelProcessFolder(currentSessionId);
    } catch (err) {
      console.error('Failed to cancel processing:', err);
    }
    setShowProgressModal(false);
    setCurrentSessionId(null);
    uploadTrackingService.disconnect();
  };

  return (
    <div
      className="w-[250px] border-r border-gray-300 bg-gray-50 dark:bg-gray-800 overflow-y-auto h-full relative"
      onClick={closeContextMenu}
    >
      <div className="h-15 flex items-center justify-between border-b border-gray-300 px-2">
        <FolderBrowseButton
          buttonText="Adauga Fisiere"
          onFolderSelect={handleFolderSelect}
          onError={(error) => console.error('File selection error:', error)}
        />
        <button
          className="ml-2 p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
          onClick={() => setIsKeyModalOpen(true)}
          title="Configure API Keys"
        >
          <FaKey />
        </button>
      </div>

      <div className="p-4">
        <button
          className="w-full mb-2 px-3 py-2 bg-blue-500 text-black rounded text-left flex items-center gap-2"
          onClick={handleNewConversationClick}
        >
          <FaSearch />
          <span className="text-sm">
            Cautare noua
          </span>
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
                className="group flex items-center px-3 py-2 flex-1 rounded border border-transparent hover:bg-gray-200"
                onClick={() => handleConversationSelect(conv.id)}
              >
                <Link
                  to={`/conversation/${conv.id}`}
                  className="flex-1 text-sm"
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

      <KeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
      />
    </div>
  );
};

export default ConversationSidebar;
