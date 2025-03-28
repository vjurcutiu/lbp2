// File: useConversationsService.js

import { useDispatch, useSelector } from 'react-redux';
import { useEffect, useCallback } from 'react';
import {
  fetchConversations,
  selectConversation,
  newConversation,
  fetchConversationMessages,
  setConversationMessages
} from '../../storage/features/conversationSlice';

/**
 * conversationId: string | undefined
 *   - "new" indicates a brand-new conversation route
 *   - a valid numeric string (e.g., "7") indicates an existing conversation ID
 *   - anything else is considered invalid and treated like a new conversation
 */
export const useConversationsService = (conversationId) => {
  const dispatch = useDispatch();
  const {
    conversations,
    activeConversationId,
    conversationMessages,
    isNewConversation
  } = useSelector((state) => state.conversations);

  // Fetch all conversations on mount.
  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  useEffect(() => {
    console.log('useConversationsService effect triggered with conversationId:', conversationId);

    // If the route param is explicitly "new", treat it as a new conversation route.
    if (conversationId === 'new') {
      console.log('Route param is "new", dispatching newConversation if not already in that state.');
      if (!isNewConversation) {
        dispatch(newConversation());
      }
      return; // Stop here, don’t attempt to parse or fetch.
    }

    // If conversationId is nonempty but not 'new', attempt to parse it.
    if (conversationId) {
      const numericId = Number(conversationId);
      if (!isNaN(numericId) && numericId > 0) {
        console.log('Valid numeric ID. Dispatching selectConversation:', numericId);
        dispatch(selectConversation(numericId));
      } else {
        console.log('conversationId is invalid, treating as new conversation...');
        if (!isNewConversation) {
          dispatch(newConversation());
        }
      }
    } else {
      // If there’s no param at all, also treat it as a new conversation.
      console.log('No conversationId provided, dispatching newConversation if needed.');
      if (!isNewConversation) {
        dispatch(newConversation());
      }
    }
  }, [conversationId, isNewConversation, dispatch]);

  // Fetch messages only if we have a valid numeric conversationId.
  useEffect(() => {
    if (conversationId && conversationId !== 'new') {
      const numericId = Number(conversationId);
      if (!isNaN(numericId) && numericId > 0) {
        console.log('Fetching messages for conversationId:', numericId);
        dispatch(fetchConversationMessages(numericId));
      }
    }
  }, [conversationId, dispatch]);

  // Custom function to update messages in Redux.
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
