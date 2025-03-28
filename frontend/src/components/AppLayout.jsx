// File: AppLayout.jsx

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import { useConversationsService } from '../services/conversations/useConversationsService';

const AppLayout = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  // Only convert to number if it’s valid.
  const conversationIdForChat =
    conversationId && !isNaN(Number(conversationId)) ? Number(conversationId) : null;
  
  // Use the custom hook to manage conversation logic.
  const { conversations, activeConversationId, conversationMessages, updateMessages } = useConversationsService(conversationId);

  // onNewMessage updates the URL to include the new conversation ID.
  const handleNewMessage = (newConversationId) => {
    // Navigate to the new conversation's route.
    navigate(`/conversation/${newConversationId}`);
  };

  return (
    <div className="flex h-full w-full">
      <div className="basis-[250px] bg-gray-100 h-full overflow-y-auto">
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
        />
      </div>
      <div className="flex-1 h-full flex flex-col overflow-y-auto">
        <ChatMetaContainer 
          conversationId={conversationIdForChat} 
          messages={conversationMessages}
          updateMessages={updateMessages}
          onNewMessage={handleNewMessage}
        />
      </div>
    </div>
  );
};

export default AppLayout;
