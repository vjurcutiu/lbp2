import { io } from "socket.io-client";
import { setConnected } from '../../features/loading/websocketSlice'


let socket = null;

export const connectSocket = (port, dispatch, options = {}) => {
    const finalPort = port || 5000;
    if (socket) {
      socket.disconnect();
    }
    socket = io(`http://localhost:${finalPort}`, options);
    socket.on("connect", () => {
      console.log("Socket connected on port", finalPort);
      if (dispatch) dispatch(setConnected(true));
    });
    socket.on("connect_error", (error) => {
      console.error("Socket connection error:", error);
      if (dispatch) dispatch(setConnected(false));
    });
    socket.on("disconnect", () => {
      console.log("Socket disconnected");
      if (dispatch) dispatch(setConnected(false));
    });
    return socket;
};
