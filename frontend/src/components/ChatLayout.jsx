// src/components/ChatLayout.jsx
import React, { useState, useEffect } from 'react';
import ConversationSidebar from './common/ConversationSidebar';
import ChatContainer from './chat/ChatContainer';
import { getConversationIds, processFolder } from '../services';

const ChatLayout = () => {
  // Start with an empty conversation list; we'll populate it via the API.
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);

  // Fetch conversation IDs from the backend on component mount.
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        // Get an array of conversation IDs from the backend.
        const ids = await getConversationIds();
        // Map the IDs to conversation objects with default titles.
        const convs = ids.map(id => ({ id, title: `Conversation ${id}` }));
        setConversations(convs);
        // Set the first conversation as active if available.
        if (convs.length > 0) {
          setActiveConversationId(convs[0].id);
        }
      } catch (error) {
        console.error("Error fetching conversation ids:", error);
      }
    };

    fetchConversations();
  }, []);

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    // You can add additional logic here if needed (for example, loading conversation details).
  };

  const handleFolderImport = (folderName) => {
    // Call your backend API using the folder name.
    processFolder({ folder_path: folderName, extension: '.txt' })
      .then((res) => {
        console.log('Folder processed:', res);
        // Optionally update your conversations list based on new data.
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
        <ChatContainer conversationId={activeConversationId} />
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
