// store.js
import { configureStore } from '@reduxjs/toolkit';
import conversationsReducer from './features/conversationSlice';
import portReducer from './features/environmentSlice';

export const store = configureStore({
  reducer: {
    conversations: conversationsReducer,
    port: portReducer,
    // add other reducers if needed
  },
});