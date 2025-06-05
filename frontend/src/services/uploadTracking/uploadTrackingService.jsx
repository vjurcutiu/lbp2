import socketService from '../websocket/socketService';
import { uploadStarted, fileUploaded, fileFailed, uploadComplete, resetUpload } from './uploadTrackingSlice';

class UploadTrackingService {
  constructor(store) {
    this.store = store;
    this.socket = null;
  }

  connect(sessionId) {
    console.log('Connecting to upload WebSocket with sessionId:', sessionId);
    if (this.socket) {
      this.socket.disconnect();
    }
    socketService.disconnect();
    socketService.connect(`http://localhost:5000/upload`, { query: `session_id=${sessionId}` });
    this.socket = socketService.socket;

    this.socket.on('connect', () => {
      console.log('Connected to upload WebSocket');
      // Join the room for this session_id to receive room-targeted events
      this.socket.emit('join', { session_id: sessionId });
      console.log('Emitted join room event for session:', sessionId);
    });

    this.socket.on('upload_started', (data) => {
      console.log('upload_started event received:', data);
      this.store.dispatch(uploadStarted({ totalFiles: data.total_files || data.totalFiles }));
      console.log('Dispatched uploadStarted action');
    });

    this.socket.on('file_uploaded', (data) => {
      console.log('file_uploaded event received:', data);
      this.store.dispatch(fileUploaded({ fileName: data.file_name || data.fileName }));
      console.log('Dispatched fileUploaded action');
    });

    this.socket.on('file_failed', (data) => {
      console.log('file_failed event received:', data);
      this.store.dispatch(fileFailed({ fileName: data.file_name || data.fileName, error: data.error }));
      console.log('Dispatched fileFailed action');
    });

    this.socket.on('upload_complete', () => {
      console.log('upload_complete event received');
      this.store.dispatch(uploadComplete());
      console.log('Dispatched uploadComplete action');
    });

    this.socket.on('test_message', (data) => {
      console.log('test_message event received:', data);
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from upload WebSocket');
    });

    // Add diagnostic log to confirm event listeners are set
    console.log('WebSocket event listeners registered');
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
