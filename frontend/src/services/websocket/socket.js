import { io } from "socket.io-client";

let socket = null;

export const connectSocket = (port, options = {}) => {
    const finalPort = port || 5000;
    if (socket) {
      socket.disconnect();
    }
    socket = io(`http://localhost:${finalPort}`, options);
    socket.on("connect", () => {
      console.log("Socket connected on port", finalPort);
    });
    socket.on("connect_error", (error) => {
      console.error("Socket connection error:", error);
    });
    return socket;
  };
