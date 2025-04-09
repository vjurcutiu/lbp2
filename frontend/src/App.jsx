import {React, useEffect} from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import RouteManager from './services/routing/RouteManager';
import './services/listeners/socketListeners';
import { setFlaskPort } from './services/storage/features/environmentSlice';
import { updateApiClientBaseURL } from './services/apiClient';
import { connectSocket } from './services/websocket/socket';
import { setupSocketListeners } from './services/listeners/socketListeners';
import { useDispatch, useSelector } from 'react-redux';


const App = () => {
  const dispatch = useDispatch();
  const flaskPort = useSelector((state) => state.port.flaskPort);

  useEffect(() => {
    console.log("First useEffect: determining port value.");
    if (
      process.env.NODE_ENV === 'development' ||
      !(
        window.electronAPI &&
        typeof window.electronAPI.onFlaskPort === 'function'
      )
    ) {
      console.warn('Defaulting to port 5000.');
      dispatch(setFlaskPort(5000));
    } else {
      console.log("electronAPI.onFlaskPort is available; waiting for port...");
      window.electronAPI.onFlaskPort((port) => {
        console.log('Received Flask port from Electron:', port);
        dispatch(setFlaskPort(port));
      });
    }
  }, [dispatch]);

  useEffect(() => {
    console.log('Second useEffect: flaskPort is', flaskPort);
    if (flaskPort) {
      console.log('Updating apiClient and socket base URL to port:', flaskPort);
      updateApiClientBaseURL(flaskPort);
      const socketInstance = connectSocket(flaskPort);
      setupSocketListeners(socketInstance);
    }
  }, [flaskPort]);

  return (
    <HashRouter>
      <Routes>
        {/* Define the route pattern for conversations. */}
        <Route path="/conversation/:conversationId" element={<RouteManager />} />
        {/* Optionally, redirect root or any other routes to a default conversation. */}
        <Route path="*" element={<Navigate to="/conversation/new" replace />} />
      </Routes>
    </HashRouter>
  );
};

export default App;
