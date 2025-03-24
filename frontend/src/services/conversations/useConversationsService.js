import { useDispatch, useSelector } from 'react-redux';
import { useEffect, useCallback } from 'react';
import {
  fetchConversations,
  selectConversation,
  newConversation,
  fetchConversationMessages,
  setConversationMessages
} from '../../storage/features/conversationSlice';

export const useConversationsService = (conversationId) => {
  const dispatch = useDispatch();
  const { conversations, activeConversationId, conversationMessages, isNewConversation } = useSelector(
    (state) => state.conversations
  );

  // Fetch conversations on mount.
  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  // Update conversation selection based on the URL's conversationId.
  useEffect(() => {
    if (conversationId) {
      dispatch(selectConversation(Number(conversationId)));
    } else {
      if (!isNewConversation) {
        dispatch(newConversation());
      }
    }
  }, [conversationId, isNewConversation, dispatch]);

  // Fetch messages for an existing conversation.
  useEffect(() => {
    if (conversationId) {
      dispatch(fetchConversationMessages(Number(conversationId)));
    }
  }, [conversationId, dispatch]);

  // Custom function to update messages.
  const updateMessages = useCallback((updater) => {
    dispatch((_, getState) => {
      const currentMessages = getState().conversations.conversationMessages;
      const newMessages = updater(currentMessages);
      dispatch(setConversationMessages(newMessages));
    });
  }, [dispatch]);

  return { conversations, activeConversationId, conversationMessages, updateMessages };
};
