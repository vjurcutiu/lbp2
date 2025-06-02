// store.js
import { configureStore } from '@reduxjs/toolkit';
import conversationsReducer from './features/conversationSlice';
import portReducer from './features/environmentSlice';
import uploadTrackingReducer from '../uploadTracking/uploadTrackingSlice';

export const store = configureStore({
  reducer: {
    conversations: conversationsReducer,
    port: portReducer,
    uploadTracking: uploadTrackingReducer,
  },
});
