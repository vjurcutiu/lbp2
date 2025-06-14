import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  totalFiles: 0,
  uploadedCount: 0,
  uploadedFiles: [],
  failedFiles: [],
  isComplete: false,
};

const uploadTrackingSlice = createSlice({
  name: 'uploadTracking',
  initialState,
  reducers: {
    uploadStarted(state, action) {
      console.log('Reducer uploadStarted called with payload:', action.payload);
      state.totalFiles = action.payload.totalFiles;
      state.uploadedCount = 0;
      state.uploadedFiles = [];
      state.failedFiles = [];
      state.isComplete = false;
      console.log('State after uploadStarted:', state);
    },
    fileUploaded(state, action) {
      console.log('Reducer fileUploaded called with payload:', action.payload);
      state.uploadedCount += 1;
      state.uploadedFiles.push(action.payload.fileName);
    },
    fileFailed(state, action) {
      console.log('Reducer fileFailed called with payload:', action.payload);
      state.uploadedCount += 1;
      state.failedFiles.push({
        fileName: action.payload.fileName,
        error: action.payload.error,
      });
    },
    uploadComplete(state) {
      console.log('Reducer uploadComplete called');
      state.isComplete = true;
    },
    resetUpload(state) {
      console.log('Reducer resetUpload called');
      Object.assign(state, initialState);
    },
  },
});

export const {
  uploadStarted,
  fileUploaded,
  fileFailed,
  uploadComplete,
  resetUpload,
} = uploadTrackingSlice.actions;

export default uploadTrackingSlice.reducer;
