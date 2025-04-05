import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import './services/listeners/socketListeners';

const App = () => {
  return (
    <HashRouter>
      <Routes>
        {/* Route for starting a new conversation */}
        <Route path="/new" element={<AppLayout />} />
        
        {/* Route for an existing conversation */}
        <Route path="/conversation/:conversationId" element={<AppLayout />} />
        
        {/* Fallback route: redirect any unknown paths to "/new" */}
        <Route path="*" element={<Navigate to="/new" replace />} />
      </Routes>
    </HashRouter>
  );
};

export default App;
