// store.js
import { configureStore } from '@reduxjs/toolkit';
import conversationsReducer from './features/conversationSlice';
import portReducer from './features/environmentSlice';
import uploadTrackingReducer from '../../features/uploadTracking/uploadTrackingSlice';
import websocketReducer from '../../features/loading/websocketSlice';

export const store = configureStore({
  reducer: {
    conversations: conversationsReducer,
    port: portReducer,
    uploadTracking: uploadTrackingReducer,
    websocket: websocketReducer,
  },
});
