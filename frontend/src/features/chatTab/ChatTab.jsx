import React from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import ConversationSidebar from '../../components/sidebar/ConversationSidebar';
import ChatMetaContainer from '../../components/chat/ChatMetaContainer';
import {useConversationsService} from '../../services/conversations/useConversationsService'; // Adjust import as needed
import { useSelector } from 'react-redux';

const ChatTab = () => {
  const navigate = useNavigate();
  const { conversationId } = useParams();

  // Get active conversation from Redux or context
  const activeConversationId = conversationId || useSelector((state) => state.conversations.activeConversationId) || "new";
  
  // Fetch/manage chat state (conversations, messages, etc)
  const {
    conversations,
    activeConversationId: activeConvIdFromService,
    conversationMessages,
    updateMessages,
  } = useConversationsService(activeConversationId);

  // Optional: Handle new message or new conversation
  const handleNewMessage = (newConversationId) => {
    navigate(`/chat/${newConversationId}`);
  };

  return (
    <div className="flex h-full overflow-hidden">
      <div className="basis-[250px] bg-gray-100 h-full overflow-y-auto">
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={activeConvIdFromService}
        />
      </div>
      <div className="flex-1 h-full flex flex-col overflow-hidden">
        <Routes>
          <Route
            path="new"
            element={
              <ChatMetaContainer
                messages={conversationMessages}
                updateMessages={updateMessages}
                onNewMessage={handleNewMessage}
                conversationId="new"
              />
            }
          />
          <Route
            path=":conversationId"
            element={
              <ChatMetaContainer
                messages={conversationMessages}
                updateMessages={updateMessages}
                onNewMessage={handleNewMessage}
                conversationId={activeConvIdFromService}
              />
            }
          />
          <Route path="*" element={<div>Select or start a conversation.</div>} />
        </Routes>
      </div>
    </div>
  );
};

export default ChatTab;

