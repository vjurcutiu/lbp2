import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getConversations,
  getConversationMessages,
  renameConversation,
  deleteConversation,
} from '../../services';

// Async thunk to fetch conversations with a console log
export const fetchConversations = createAsyncThunk(
  'conversations/fetchConversations',
  async () => {
    console.log('Fetching conversations...');
    const convs = await getConversations();
    console.log('Retrieved conversations:', convs);
    return convs;
  }
);

// Async thunk to fetch messages for a conversation with a log
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
    // Set active conversation
    selectConversation: (state, action) => {
      console.log('Selecting conversation:', action.payload);
      state.activeConversationId = action.payload;
      state.isNewConversation = false;
      state.conversationMessages = [];
    },
    // Start new conversation
    newConversation: (state) => {
      console.log('Starting a new conversation');
      state.activeConversationId = null;
      state.conversationMessages = [];
      state.isNewConversation = true;
    },
    renameConversationLocal: (state, action) => {
      const { conversationId, newTitle } = action.payload;
      const conversation = state.conversations.find(conv => conv.id === conversationId);
      if (conversation) {
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
  renameConversationLocal,
  deleteConversationLocal,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;
