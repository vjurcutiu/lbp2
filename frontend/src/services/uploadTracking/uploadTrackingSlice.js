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
      state.totalFiles = action.payload.totalFiles;
      state.uploadedCount = 0;
      state.uploadedFiles = [];
      state.failedFiles = [];
      state.isComplete = false;
    },
    fileUploaded(state, action) {
      state.uploadedCount += 1;
      state.uploadedFiles.push(action.payload.fileName);
    },
    fileFailed(state, action) {
      state.uploadedCount += 1;
      state.failedFiles.push({
        fileName: action.payload.fileName,
        error: action.payload.error,
      });
    },
    uploadComplete(state) {
      state.isComplete = true;
    },
    resetUpload(state) {
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
