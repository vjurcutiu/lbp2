import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/AppLayout';

const App = () => {
  return (
    <HashRouter>
      <Routes>
        {/* Route for starting a new conversation */}
        <Route path="/new" element={<AppLayout />} />
        
        {/* Route for an existing conversation */}
        <Route path="/conversation/:conversationId" element={<AppLayout />} />
        
        {/* Fallback route */}
        <Route path="" element={<AppLayout />} />
      </Routes>
    </HashRouter>
  );
};

export default App;