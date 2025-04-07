import socket from '../websocket/socket';
import { store } from '../storage/store';
import {
  setConversations,
  setNewConversationId,
  renameConversationLocal,
  updateConversationLocal
} from '../storage/features/conversationSlice';

// Listen for conversation list updates
socket.on("conversation_list", (newList) => {
  console.log('received new list', newList);
  store.dispatch(setConversations(newList));
});

// Listen for new conversation events
socket.on("new_conversation", (newConversation) => {
  store.dispatch(setNewConversationId(newConversation.id));
});

// Listen for conversation title updates
socket.on("conversation_title", (data) => {
  console.log('Received updated conversation title:', data);
  store.dispatch(renameConversationLocal({ conversationId: data.id, newTitle: data.title }));
});

// Listen for generic conversation updates
socket.on("conversation_update", (data) => {
  console.log("Received conversation update:", data);
  store.dispatch(updateConversationLocal(data));
});
