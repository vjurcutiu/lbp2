import React from 'react';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import { useConversationsService } from '../services/conversations/useConversationsService';
import { useNavigation } from '../services/routing/NavigationContext';

const AppLayout = ({ conversationId }) => {
  const { setConversationId } = useNavigation();

  const conversationIdForChat =
    conversationId === "new"
      ? "new"
      : (!isNaN(Number(conversationId)) ? Number(conversationId) : null);

  const { conversations, activeConversationId, conversationMessages, updateMessages } =
    useConversationsService(conversationId);

  const handleNewMessage = (newConversationId) => {
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
