// src/components/ChatLayout.jsx
import React, { useState, useEffect } from 'react';
import ConversationSidebar from './common/ConversationSidebar';
import ChatContainer from './chat/ChatContainer';
import { getConversationIds, getConversationMessages, processFolder } from '../services';

const ChatLayout = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);

  // Fetch conversation IDs on mount.
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const ids = await getConversationIds();
        // Map IDs to conversation objects with default titles.
        const convs = ids.map(id => ({ id, title: `Conversation ${id}` }));
        setConversations(convs);
        if (convs.length > 0) {
          setActiveConversationId(convs[0].id);
        }
      } catch (error) {
        console.error("Error fetching conversation ids:", error);
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
    }
  }, [activeConversationId]);

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    // The useEffect hook above will fetch messages for the new conversation.
  };

  const handleFolderImport = (folderName) => {
    processFolder({ folder_path: folderName, extension: '.txt' })
      .then((res) => {
        console.log('Folder processed:', res);
        // Optionally, update your conversation list if needed.
      })
      .catch((err) => console.error('Error processing folder:', err));
  };

  return (
    <div style={layoutStyles.container}>
      <ConversationSidebar
        conversations={conversations}
        onSelect={handleSelectConversation}
        activeConversationId={activeConversationId}
        onFolderImport={handleFolderImport}
      />
      <div style={layoutStyles.chatArea}>
        <ChatContainer 
          conversationId={activeConversationId} 
          messages={conversationMessages}
          updateMessages={setConversationMessages}  // Pass the parent's state updater
        />
      </div>
    </div>
  );
};

const layoutStyles = {
  container: {
    display: 'flex',
    height: '100vh',
    width: '100%',
  },
  chatArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
};

export default ChatLayout;
