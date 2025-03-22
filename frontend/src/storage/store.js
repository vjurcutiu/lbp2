// store.js
import { configureStore } from '@reduxjs/toolkit';
import conversationsReducer from './features/conversationSlice';

export const store = configureStore({
  reducer: {
    conversations: conversationsReducer,
    // add other reducers if needed
  },
});