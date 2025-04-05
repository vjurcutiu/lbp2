import { useDispatch, useSelector } from 'react-redux';
import { useEffect, useCallback, useRef } from 'react';
import {
  fetchConversations,
  selectConversation,
  newConversation,
  fetchConversationMessages,
  setConversationMessages
} from '../../storage/features/conversationSlice';

export const useConversationsService = (conversationId) => {
  const dispatch = useDispatch();
  const {
    conversations,
    activeConversationId,
    conversationMessages,
    isNewConversation
  } = useSelector((state) => state.conversations);
  const hasDispatchedNewConversation = useRef(false);

  // Fetch all conversations on mount.
  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  useEffect(() => {
    console.log('useConversationsService effect triggered with conversationId:', conversationId);

    // Handle undefined or "new" conversationId.
    if (conversationId === undefined || conversationId === 'new') {
      console.log('No valid conversationId provided or route param is "new".');
      if (!isNewConversation && !hasDispatchedNewConversation.current) {
        dispatch(newConversation());
        hasDispatchedNewConversation.current = true;
      }
      return;
    }

    // Otherwise, parse the conversationId.
    const numericId = Number(conversationId);
    if (!isNaN(numericId) && numericId > 0) {
      console.log('Valid numeric ID. Dispatching selectConversation:', numericId);
      dispatch(selectConversation(numericId));
    } else {
      console.log('conversationId is invalid, treating as new conversation...');
      if (!isNewConversation && !hasDispatchedNewConversation.current) {
        dispatch(newConversation());
        hasDispatchedNewConversation.current = true;
      }
    }
  }, [conversationId, isNewConversation, dispatch]);

  useEffect(() => {
    if (conversationId && conversationId !== 'new') {
      const numericId = Number(conversationId);
      if (!isNaN(numericId) && numericId > 0) {
        console.log('Fetching messages for conversationId:', numericId);
        dispatch(fetchConversationMessages(numericId));
      }
    }
  }, [conversationId, dispatch]);

  const updateMessages = useCallback(
    (updater) => {
      dispatch((_, getState) => {
        const currentMessages = getState().conversations.conversationMessages;
        const newMessages = updater(currentMessages);
        dispatch(setConversationMessages(newMessages));
      });
    },
    [dispatch]
  );

  return {
    conversations,
    activeConversationId,
    conversationMessages,
    updateMessages
  };
};
