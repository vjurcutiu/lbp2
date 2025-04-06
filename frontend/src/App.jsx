import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import RouteManager from './services/routing/RouteManager';
import './services/listeners/socketListeners';

const App = () => {
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
