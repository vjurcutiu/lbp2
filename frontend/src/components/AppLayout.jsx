import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import { useConversationsService } from '../services/conversations/useConversationsService';

const AppLayout = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [hasRedirected, setHasRedirected] = useState(false);

  useEffect(() => {
    if (conversationId === undefined && !hasRedirected) {
      setHasRedirected(true);
      navigate('/conversation/new', { replace: true });
    }
  }, [conversationId, navigate, hasRedirected]);

  // Convert conversationId to proper type.
  const conversationIdForChat =
    conversationId === 'new'
      ? 'new'
      : (conversationId && !isNaN(Number(conversationId)) ? Number(conversationId) : null);

  const { conversations, activeConversationId, conversationMessages, updateMessages } =
    useConversationsService(conversationId);

  const handleNewMessage = (newConversationId) => {
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
