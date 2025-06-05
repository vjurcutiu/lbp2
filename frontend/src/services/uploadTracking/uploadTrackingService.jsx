import socketService from '../websocket/socketService';
import { uploadStarted, fileUploaded, fileFailed, uploadComplete, resetUpload } from './uploadTrackingSlice';

class UploadTrackingService {
  constructor(store) {
    this.store = store;
    this.socket = null;
  }

  connect(sessionId) {
    if (this.socket) {
      this.socket.disconnect();
    }
    socketService.connect(`http://localhost:5000/upload?session_id=${sessionId}`);
    this.socket = socketService.socket;
    this.socket.on('connect', () => {
      console.log('Connected to upload WebSocket');
    });
    this.socket.on('upload_started', (data) => {
      this.store.dispatch(uploadStarted({ totalFiles: data.total_files || data.totalFiles }));
    });
    this.socket.on('file_uploaded', (data) => {
      this.store.dispatch(fileUploaded({ fileName: data.file_name || data.fileName }));
    });
    this.socket.on('file_failed', (data) => {
      this.store.dispatch(fileFailed({ fileName: data.file_name || data.fileName, error: data.error }));
    });
    this.socket.on('upload_complete', () => {
      this.store.dispatch(uploadComplete());
    });
    this.socket.on('disconnect', () => {
      console.log('Disconnected from upload WebSocket');
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  startUpload(folderPaths, extensions) {
    // Call the existing folderApi to start the upload, but now use WebSocket for progress
    // This method should be adapted to your existing API call structure
    // For example, you might call folderApi.processFolder and then connect to WebSocket with sessionId
    // This is a placeholder for integration
  }

  cancelUpload(sessionId) {
    // Implement cancellation logic if needed, e.g., call folderApi.cancelProcessFolder
  }
}

export default UploadTrackingService;
