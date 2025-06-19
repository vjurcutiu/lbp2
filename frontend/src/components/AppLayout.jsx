import React from 'react';
import TitleBar from './TitleBar';

const AppLayout = ({ children }) => (
  <div className="flex h-screen flex-col overflow-hidden">
    <TitleBar />
    <div className="flex-1 overflow-hidden">
      {children}
    </div>
  </div>
);

export default AppLayout;
