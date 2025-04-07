import socket from '../websocket/socket';
import { store } from '../storage/store';
import { setConversations, setNewConversationId,renameConversationLocal } from '../storage/features/conversationSlice';

// Listen for conversation list updates
socket.on("conversation_list", (newList) => {
  // newList is expected to be the updated conversation list from the backend
  console.log('received new list', newList);
  store.dispatch(setConversations(newList));
});

// Listen for new conversation events
socket.on("new_conversation", (newConversation) => {
  // newConversation should include at least an 'id' field
  store.dispatch(setNewConversationId(newConversation.id));
  // Optionally update the conversation list if needed
  // store.dispatch(setConversations(newConversation.updatedList));
});

// Listen for conversation title updates
socket.on("conversation_title", (data) => {
  console.log('Received updated conversation title:', data);
  // Dispatch an action to update the conversation title in the Redux store.
  // Assuming renameConversationLocal expects a payload with conversationId and newTitle.
  store.dispatch(renameConversationLocal({ conversationId: data.id, newTitle: data.title }));
});