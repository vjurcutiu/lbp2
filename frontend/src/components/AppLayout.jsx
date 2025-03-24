import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import ConversationSidebar from './sidebar/ConversationSidebar';
import ChatMetaContainer from './chat/ChatMetaContainer';
import {
  fetchConversations,
  selectConversation,
  newConversation,
  fetchConversationMessages,
} from '../storage/features/conversationSlice';

const AppLayout = () => {
  const { conversationId } = useParams();
  const dispatch = useDispatch();
  const { conversations, activeConversationId, conversationMessages } = useSelector(
    (state) => state.conversations
  );

  // Log the conversationId from the URL for debugging
  useEffect(() => {
    console.log('URL conversationId:', conversationId);
  }, [conversationId]);

  // Fetch conversations on mount
  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  // Update Redux state based on the URL parameter
  useEffect(() => {
    if (conversationId) {
      console.log('Dispatching selectConversation for id:', conversationId);
      dispatch(selectConversation(Number(conversationId)));
    } else {
      console.log('Dispatching newConversation because no conversationId is provided');
      dispatch(newConversation());
    }
  }, [conversationId, dispatch]);

  // Fetch messages when a conversation is selected
  useEffect(() => {
    if (conversationId) {
      console.log('Dispatching fetchConversationMessages for id:', conversationId);
      dispatch(fetchConversationMessages(Number(conversationId)));
    }
  }, [conversationId, dispatch]);

  const conversationIdForChat = conversationId ? Number(conversationId) : null;
  console.log('Active conversationId for ChatMetaContainer:', conversationIdForChat);

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
        />
      </div>
    </div>
  );
};

export default AppLayout;
