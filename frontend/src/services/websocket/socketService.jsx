import io from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.heartbeatInterval = null;
  }

  // Connect to the Socket.IO server at the provided URL
  connect(url, options = {}) {
    // Always create a new connection, disconnecting existing one if any
    console.log("Connecting socket to:", url, options);
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.socket = io(url, {
      transports: ['websocket'],
      ...options,
    });
    if (options.auth) {
      this.socket.auth = { ...options.auth };
    }
    this.socket.on('connect', () => {
      console.log('Connected to Socket.IO server');
      // Start sending heartbeat pings every 25 seconds to keep connection alive
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
      }
      this.heartbeatInterval = setInterval(() => {
        if (this.socket && this.socket.connected) {
          this.socket.emit('heartbeat', { timestamp: Date.now() });
          console.log('Sent heartbeat ping');
        }
      }, 25000);
    });
    this.socket.on('disconnect', () => {
      console.log('Disconnected from Socket.IO server');
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
    });
  }

  // Disconnect from the Socket.IO server
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
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
