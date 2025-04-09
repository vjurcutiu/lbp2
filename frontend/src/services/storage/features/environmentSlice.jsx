// features/environmentSlice.js
import { createSlice } from '@reduxjs/toolkit';

export const environmentSlice = createSlice({
  name: 'port',
  initialState: {
    flaskPort: null,
  },
  reducers: {
    setFlaskPort: (state, action) => {
      state.flaskPort = action.payload;
    },
  },
});

export const { setFlaskPort } = environmentSlice.actions;
export default environmentSlice.reducer;
