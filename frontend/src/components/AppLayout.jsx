import React from 'react';
import { useSelector } from 'react-redux';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import TitleBar from './TitleBar'; // Import your title bar component
import { useConversationsService } from '../services/conversations/useConversationsService';
import { useNavigation } from '../services/routing/NavigationContext';

const AppLayout = () => {
  const { setConversationId } = useNavigation();
  const activeConversationId = useSelector(
    (state) => state.conversations.activeConversationId
  );
  const conversationIdForChat = activeConversationId ? activeConversationId : "new";

  const {
    conversations,
    activeConversationId: activeConvIdFromService,
    conversationMessages,
    updateMessages
  } = useConversationsService(conversationIdForChat);

  const activeIdForSidebar = conversationIdForChat === "new" ? null : activeConvIdFromService;

  const handleNewMessage = (newConversationId) => {
    // your logic here
  };

  return (
    <div className="flex h-full flex-col">
      <TitleBar /> {/* This is your custom titlebar */}
      <div className="flex flex-1">
        <div className="basis-[250px] bg-gray-100 h-full overflow-y-auto">
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={activeIdForSidebar}
          />
        </div>
        <div className="flex-1 h-full flex flex-col overflow-y-auto">
          <ChatMetaContainer 
            messages={conversationMessages}
            updateMessages={updateMessages}
            onNewMessage={handleNewMessage}
          />
        </div>
      </div>
    </div>
  );
};

export default AppLayout;
