import React, { useState, useEffect } from 'react';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import { getConversations, getConversationMessages, processFolder, deleteConversation, renameConversation } from '../services';

const ChatLayout = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);
  const [isNewConversation, setIsNewConversation] = useState(false);

  // Fetch conversations on mount.
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const convs = await getConversations();
        setConversations(convs);
      } catch (error) {
        console.error("Error fetching conversations:", error);
      }
    };
    fetchConversations();
  }, []);

  // Fetch messages whenever the active conversation changes.
  useEffect(() => {
    if (activeConversationId) {
      const fetchMessages = async () => {
        try {
          const msgs = await getConversationMessages(activeConversationId);
          setConversationMessages(msgs);
        } catch (error) {
          console.error("Error fetching conversation messages:", error);
          setConversationMessages([]);
        }
      };
      fetchMessages();
    } else {
      setConversationMessages([]);
    }
  }, [activeConversationId]);

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    setIsNewConversation(false);
  };

  // Handler for new conversation button
  const handleNewConversation = () => {
    setActiveConversationId(null);
    setConversationMessages([]);
    setIsNewConversation(true);
  };

  const handleFolderImport = (folderName) => {
    processFolder({ folder_path: folderName, extension: '.txt' })
      .then((res) => {
        console.log('Folder processed:', res);
      })
      .catch((err) => console.error('Error processing folder:', err));
  };

  const handleRenameConversation = async (conversation, newTitle) => {
    try {
      const result = await renameConversation(conversation.id, newTitle);
      console.log(result);
      setConversations((prevConvs) =>
        prevConvs.map((conv) =>
          conv.id === conversation.id ? { ...conv, title: newTitle } : conv
        )
      );
    } catch (error) {
      console.error('Error renaming conversation:', error);
    }
  };

  const handleDeleteConversation = async (conversation) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    try {
      const result = await deleteConversation(conversation.id);
      console.log(result);
      setConversations((prevConvs) => prevConvs.filter((conv) => conv.id !== conversation.id));
      if (activeConversationId === conversation.id) {
        setActiveConversationId(null);
        setConversationMessages([]);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  // New function to refresh conversation list.
  const refreshConversations = async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Error refreshing conversations:", error);
    }
  };

  return (
    <div className="flex h-full w-full">
      <div className="basis-[250px] bg-gray-100 h-full overflow-y-auto">
        <ConversationSidebar
          conversations={conversations}
          onSelect={handleSelectConversation}
          activeConversationId={activeConversationId}
          onFolderImport={handleFolderImport}
          onRenameConversation={handleRenameConversation}
          onDeleteConversation={handleDeleteConversation}
          onNewConversation={handleNewConversation}
        />
      </div>
      <div className="flex-1 h-full flex flex-col overflow-y-auto">
        <ChatMetaContainer 
          conversationId={activeConversationId} 
          messages={conversationMessages}
          updateMessages={setConversationMessages}
          isNewConversation={isNewConversation}
          onNewMessage={refreshConversations}  
        />
      </div>
    </div>
  );
};

export default ChatLayout;
