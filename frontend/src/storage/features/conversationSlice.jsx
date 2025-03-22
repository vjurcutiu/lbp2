// conversationsSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { getConversations, getConversationMessages, renameConversation, deleteConversation } from '../../services';

// Async thunk to fetch conversations
export const fetchConversations = createAsyncThunk(
  'conversations/fetchConversations',
  async () => {
    const convs = await getConversations();
    return convs;
  }
);

// Async thunk to fetch messages for a conversation
export const fetchConversationMessages = createAsyncThunk(
  'conversations/fetchConversationMessages',
  async (conversationId) => {
    const msgs = await getConversationMessages(conversationId);
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
    // Synchronous actions
    selectConversation: (state, action) => {
      state.activeConversationId = action.payload;
      state.isNewConversation = false;
      state.conversationMessages = [];
    },
    newConversation: (state) => {
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
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.conversations = action.payload;
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(fetchConversationMessages.fulfilled, (state, action) => {
        // Only update messages if the fetched conversation matches the active one
        if (state.activeConversationId === action.payload.conversationId) {
          state.conversationMessages = action.payload.messages;
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
