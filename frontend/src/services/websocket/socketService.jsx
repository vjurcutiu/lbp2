import io from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
  }

  // Connect to the Socket.IO server at the provided URL
  connect(url, options = {}) {
    // Always create a new connection, disconnecting existing one if any
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.socket = io(url, {
      transports: ['websocket'],
      ...options,
    });
    this.socket.on('connect', () => {
      console.log('Connected to Socket.IO server');
    });
  }

  // Disconnect from the Socket.IO server
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log('Disconnected from Socket.IO server');
    }
  }

  // Subscribe to a given event with a callback
  subscribeToEvent(eventName, callback) {
    if (this.socket) {
      this.socket.on(eventName, callback);
    } else {
      console.error('Socket is not connected. Call connect() first.');
    }
  }

  // Unsubscribe from a given event
  unsubscribeFromEvent(eventName) {
    if (this.socket) {
      this.socket.off(eventName);
    }
  }

  // Send a message using a specific event name
  sendMessage(eventName, message) {
    if (this.socket) {
      this.socket.emit(eventName, message);
    } else {
      console.error('Socket is not connected. Call connect() first.');
    }
  }
}

// Export a single instance of SocketService to use across your app
const socketService = new SocketService();
export default socketService;
