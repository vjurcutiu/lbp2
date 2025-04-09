// socketListeners.js
import { store } from '../storage/store';
import {
  setConversations,
  setNewConversationId,
  renameConversationLocal,
  updateConversationLocal
} from '../storage/features/conversationSlice';

export const setupSocketListeners = (socketInstance) => {
  if (!socketInstance) {
    console.error('No socket instance provided to register listeners.');
    return;
  }
  
  socketInstance.on("conversation_list", (newList) => {
    console.log("Listener log: received 'conversation_list' with payload:", newList);
    store.dispatch(setConversations(newList));
  });

  socketInstance.on("new_conversation", (newConversation) => {
    console.log("Listener log: received 'new_conversation' with payload:", newConversation);
    store.dispatch(setNewConversationId(newConversation.id));
  });

  socketInstance.on("conversation_title", (data) => {
    console.log("Listener log: received 'conversation_title' with payload:", data);
    store.dispatch(renameConversationLocal({ conversationId: data.id, newTitle: data.title }));
  });

  socketInstance.on("conversation_update", (data) => {
    console.log("Listener log: received 'conversation_update' with payload:", data);
    store.dispatch(updateConversationLocal(data));
  });
};
