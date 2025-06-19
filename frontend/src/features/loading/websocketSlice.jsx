import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isConnected: false,
};

const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    setConnected: (state, action) => {
      state.isConnected = action.payload;
    },
  },
});

export const { setConnected } = websocketSlice.actions;
export default websocketSlice.reducer;
