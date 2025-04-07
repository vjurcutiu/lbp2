import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getConversations,
  getConversationMessages,
  renameConversation,
  deleteConversation,
} from '../..';

export const fetchConversations = createAsyncThunk(
  'conversations/fetchConversations',
  async () => {
    console.log('Fetching conversations...');
    const convs = await getConversations();
    console.log('Retrieved conversations:', convs);
    return convs;
  }
);

export const generateNewConversationThunk = () => (dispatch, getState) => {
  const { conversations } = getState().conversations;
  const newId = Math.max(...conversations.map((c) => c.id), 0) + 1;
  dispatch(generateNewConversation(newId));
  return newId;
};

export const fetchConversationMessages = createAsyncThunk(
  'conversations/fetchConversationMessages',
  async (conversationId) => {
    console.log('Fetching messages for conversationId:', conversationId);
    const msgs = await getConversationMessages(conversationId);
    console.log('Retrieved messages:', msgs);
    return { conversationId, messages: msgs };
  }
);

const conversationsSlice = createSlice({
  name: 'conversations',
  initialState: {
    conversations: [],
    activeConversationId: null,
    conversationMessages: [],
    isNewConversation: false,
    status: 'idle',
    error: null,
  },
  reducers: {
    selectConversation: (state, action) => {
      console.log('Selecting conversation:', action.payload);
      state.activeConversationId = action.payload;
      state.isNewConversation = false;
      state.conversationMessages = [];
    },
    setConversations: (state, action) => {
      console.log('Updating conversation list:', action.payload);
      state.conversations = action.payload;
    },
    newConversation: (state) => {
      console.log('Starting a new conversation');
      state.activeConversationId = null;
      state.conversationMessages = [];
      state.isNewConversation = true;
    },
    setConversationMessages: (state, action) => {
      console.log('Updating conversation messages:', action.payload);
      state.conversationMessages = action.payload;
    },
    renameConversationLocal: (state, action) => {
      const { conversationId, newTitle } = action.payload;
      const conversation = state.conversations.find(conv => conv.id === conversationId);
      if (conversation) {
        console.log(`Conversation ${conversationId} title updated to: ${newTitle}`);
        conversation.title = newTitle;
      }
    },
    deleteConversationLocal: (state, action) => {
      const conversationId = action.payload;
      state.conversations = state.conversations.filter(conv => conv.id !== conversationId);
      if (state.activeConversationId === conversationId) {
        state.activeConversationId = null;
        state.conversationMessages = [];
      }
    },
    setNewConversationId: (state, action) => {
      console.log('Reducer received new conversation ID:', action.payload);
      state.activeConversationId = action.payload;
      state.isNewConversation = false;
    },
    clearNewConversationId: (state) => {
      console.log('Clearing new conversation state');
      state.activeConversationId = null;
      state.isNewConversation = false;
    },
    clearActiveConversation: (state) => {
      console.log('Clearing active conversation state');
      state.activeConversationId = null;
      state.isNewConversation = true;
    },
    generateNewConversation: (state) => {
      const maxId = state.conversations.reduce(
        (max, conv) => (conv.id > max ? conv.id : max),
        0
      );
      const newId = maxId + 1;
      state.activeConversationId = newId;
      state.conversationMessages = [];
      state.isNewConversation = true;
    },
    updateConversationLocal: (state, action) => {
      const updatedConversation = action.payload;
      const conversation = state.conversations.find(conv => conv.id === updatedConversation.id);
      if (conversation) {
        Object.assign(conversation, updatedConversation);
        console.log(`Conversation ${updatedConversation.id} updated with:`, updatedConversation);
      }
    },
    
  },     
  extraReducers: (builder) => {
    builder
      .addCase(fetchConversations.pending, (state) => {
        state.status = 'loading';
        console.log('fetchConversations pending...');
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.conversations = action.payload;
        console.log('fetchConversations fulfilled. Conversations:', action.payload);
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
        console.error('fetchConversations failed:', action.error.message);
      })
      .addCase(fetchConversationMessages.fulfilled, (state, action) => {
        if (state.activeConversationId === action.payload.conversationId) {
          state.conversationMessages = action.payload.messages;
          console.log('Updated conversation messages for conversationId:', action.payload.conversationId);
        }
      });
  },
});

export const {
  selectConversation,
  newConversation,
  setConversationMessages,
  renameConversationLocal,
  deleteConversationLocal,
  setNewConversationId,
  setConversations,
  clearActiveConversation,
  generateNewConversation,
  updateConversationLocal, // Export the new action
} = conversationsSlice.actions;

export default conversationsSlice.reducer;
