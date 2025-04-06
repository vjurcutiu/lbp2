import { useDispatch, useSelector } from 'react-redux';
import { useEffect, useCallback, useRef } from 'react';
import {
  selectConversation,
  newConversation,
  fetchConversationMessages,
  setConversationMessages,
  fetchConversations // ensure you have this thunk defined and exported
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

  // Fallback: if the conversations array is empty, fetch them.
  useEffect(() => {
    if (conversations.length === 0) {
      console.log('Conversations array is empty. Fetching conversations...');
      dispatch(fetchConversations());
    }
  }, [conversations, dispatch]);

  // Determine the effective conversationId.
  const effectiveConversationId =
    (conversationId === 'new' && activeConversationId !== null)
      ? activeConversationId
      : conversationId;

  useEffect(() => {
    console.log(
      'useConversationsService effect triggered with route conversationId:',
      conversationId,
      'and activeConversationId:',
      activeConversationId
    );

    if (effectiveConversationId === undefined || effectiveConversationId === 'new') {
      console.log('No valid conversationId provided or still "new".');
      if (!isNewConversation && !hasDispatchedNewConversation.current) {
        dispatch(newConversation());
        hasDispatchedNewConversation.current = true;
      }
      return;
    }

    const numericId = Number(effectiveConversationId);
    if (!isNaN(numericId) && numericId > 0) {
      console.log('Valid numeric ID. Dispatching selectConversation:', numericId);
      dispatch(selectConversation(numericId));
    } else {
      console.log('effectiveConversationId is invalid, treating as new conversation...');
      if (!isNewConversation && !hasDispatchedNewConversation.current) {
        dispatch(newConversation());
        hasDispatchedNewConversation.current = true;
      }
    }
  }, [
    conversationId,
    activeConversationId,
    isNewConversation,
    dispatch,
    effectiveConversationId
  ]);

  useEffect(() => {
    if (effectiveConversationId && effectiveConversationId !== 'new') {
      const numericId = Number(effectiveConversationId);
      if (!isNaN(numericId) && numericId > 0) {
        console.log('Fetching messages for conversationId:', numericId);
        dispatch(fetchConversationMessages(numericId));
      }
    }
  }, [effectiveConversationId, dispatch]);

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
