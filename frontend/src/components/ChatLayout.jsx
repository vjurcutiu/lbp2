// src/components/ChatLayout.jsx
import React, { useState } from 'react';
import ConversationSidebar from './common/ConversationSidebar';
import ChatContainer from './chat/ChatContainer';
import { processFolder } from '../services/api'; // your API call for processing folder

const ChatLayout = () => {
  const [conversations, setConversations] = useState([
    { id: 1, title: 'Support Chat' },
    { id: 2, title: 'Project Discussion' },
    { id: 3, title: 'Random Chat' },
  ]);
  const [activeConversationId, setActiveConversationId] = useState(conversations[0].id);

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    // Load the selected conversation's details if needed
  };

  const handleFolderImport = (folderName) => {
    // Call your backend API using the folderName
    // For example, using the processFolder API function:
    processFolder({ folder_path: folderName, extension: '.txt' })
      .then((res) => {
        console.log('Folder processed:', res);
        // Optionally update your conversations list based on the new data
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
