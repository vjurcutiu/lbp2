// store.js
import { configureStore } from '@reduxjs/toolkit';
import rootReducer from './reducers'; // Combine your reducers here

const store = configureStore({
  reducer: rootReducer,
});

export default store;
