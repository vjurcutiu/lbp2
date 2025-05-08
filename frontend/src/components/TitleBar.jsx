import React from 'react';
import './TitleBar.css'; // Import CSS for styles
import { MdMinimize, MdCropSquare, MdClose } from 'react-icons/md';

const TitleBar = () => {
  // Function to minimize the window
  const handleMinimize = () => {
    if (window.electronAPI && window.electronAPI.minimizeWindow) {
      window.electronAPI.minimizeWindow();
    }
  };

  // Function to toggle maximize/restore the window
  const handleMaximize = () => {
    if (window.electronAPI && window.electronAPI.maximizeWindow) {
      window.electronAPI.maximizeWindow();
    }
  };

  // Function to close the window
  const handleClose = () => {
    if (window.electronAPI && window.electronAPI.closeWindow) {
      window.electronAPI.closeWindow();
    }
  };

  return (
    <div className="titlebar">
      <div className="title">LexBot PRO</div>
      <div className="window-controls">
        <button className="minimize" onClick={handleMinimize} aria-label="Minimize">
          <MdMinimize size={20} />
        </button>
        <button className="maximize" onClick={handleMaximize} aria-label="Maximize">
          <MdCropSquare size={20} />
        </button>
        <button className="close" onClick={handleClose} aria-label="Close">
          <MdClose size={20} />
        </button>
      </div>
    </div>
  );
};

export default TitleBar;
