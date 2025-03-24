import React from 'react';
import { useParams } from 'react-router-dom';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import { useConversationsService } from '../services/conversations/useConversationsService';

const AppLayout = () => {
  const { conversationId } = useParams();
  const conversationIdForChat = conversationId ? Number(conversationId) : null;
  
  // Use the custom hook to manage conversation logic.
  const { conversations, activeConversationId, conversationMessages, updateMessages } = useConversationsService(conversationId);

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
        />
      </div>
    </div>
  );
};

export default AppLayout;
