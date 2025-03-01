/**
 * ChatLayout Component
 *
 * This component serves as the main layout for the chat application.
 * It orchestrates the conversation sidebar and the chat container to provide
 * a complete chat interface.
 *
 * Functionality:
 * - Fetches and displays a list of conversation IDs in the ConversationSidebar.
 * - Allows the user to select an active conversation, which triggers fetching of
 *   the corresponding messages.
 * - Integrates the ChatContainer to display the conversation's messages and handle
 *   message sending.
 * - Supports folder import functionality to process chat files via the onFolderImport handler.
 *
 * The component leverages useEffect hooks to manage data fetching on mount and when
 * the active conversation changes.
 *
 * Layout:
 * - The sidebar has a base width of 250px.
 * - The chat area fills the remaining space.
 */
import React, { useState, useEffect } from 'react';
import ConversationSidebar from './common/ConversationSidebar';
import ChatContainer from './chat/ChatContainer';
import { getConversationIds, getConversationMessages, processFolder } from '../services';

const ChatLayout = () => {
  const [conversations, setConversations] = useState([]);
  // Start with no active conversation
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
        // Instead of auto-selecting an existing conversation, start fresh.
        // if (convs.length > 0) {
        //   setActiveConversationId(convs[0].id);
        // }
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
    } else {
      // When there's no active conversation, ensure we have an empty conversation
      setConversationMessages([]);
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
    <div className="flex h-full w-full">
      <div className="basis-[250px] bg-gray-100 h-full overflow-y-auto">
        <ConversationSidebar
          conversations={conversations}
          onSelect={handleSelectConversation}
          activeConversationId={activeConversationId}
          onFolderImport={handleFolderImport}
        />
      </div>
      <div className="flex-1 h-full flex flex-col overflow-y-auto">
        <ChatContainer 
          conversationId={activeConversationId} 
          messages={conversationMessages}
          updateMessages={setConversationMessages}  // Pass the parent's state updater
        />
      </div>
    </div>
  );
};

export default ChatLayout;
