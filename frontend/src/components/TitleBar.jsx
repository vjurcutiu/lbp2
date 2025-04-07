import React from 'react';
import './TitleBar.css'; // Import CSS for styles

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
        <button className="minimize" onClick={handleMinimize}>
          &#x2013;
        </button>
        <button className="maximize" onClick={handleMaximize}>
          &#9633;
        </button>
        <button className="close" onClick={handleClose}>
          &#x2715;
        </button>
      </div>
    </div>
  );
};

export default TitleBar;
