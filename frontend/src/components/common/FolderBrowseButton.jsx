// src/components/common/FolderBrowseButton.jsx
import React, { useRef } from 'react';
import PropTypes from 'prop-types';

const FolderBrowseButton = ({ onFolderSelect, buttonText, onError }) => {
  // Check if we're running in Electron by detecting the exposed API
  const isElectron = !!(window.electronAPI && window.electronAPI.selectFolderOrFile);
  const fileInputRef = useRef(null);

  // This function is used when running in Electron
  const handleElectronSelect = async () => {
    try {
      const selectedPaths = await window.electronAPI.selectFolderOrFile();
      if (selectedPaths && selectedPaths.length > 0) {
        // If one item is selected, pass it as a string; if multiple, pass the array.
        if (selectedPaths.length === 1) {
          onFolderSelect(selectedPaths[0]);
        } else {
          onFolderSelect(selectedPaths);
        }
      } else {
        throw new Error("No files or folders selected.");
      }
    } catch (error) {
      console.error("Error selecting folder or file:", error);
      if (onError) onError(error);
    }
  };

  // This function is used when not in Electron (i.e., fallback for browsers)
  const handleBrowserSelect = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    } else {
      const error = new Error("File input element not found.");
      console.error(error);
      if (onError) onError(error);
    }
  };

  // Decide which handler to use when the button is clicked
  const handleClick = async () => {
    if (isElectron) {
      await handleElectronSelect();
    } else {
      handleBrowserSelect();
    }
  };

  // Fallback handler for when a file is selected in the browser
  const handleChange = (e) => {
    try {
      const files = e.target.files;
      if (!files || files.length === 0) {
        throw new Error("No files selected.");
      }
      // Process the FileList. For example, return an array of file names:
      const selectedPaths = [];
      for (let i = 0; i < files.length; i++) {
        // In a browser, you typically get only file names (and relative paths if webkitdirectory is used)
        selectedPaths.push(files[i].name);
      }
      // If only one file is selected, send it as a string; otherwise, send the array.
      if (selectedPaths.length === 1) {
        onFolderSelect(selectedPaths[0]);
      } else {
        onFolderSelect(selectedPaths);
      }
    } catch (error) {
      console.error("Error in FolderBrowseButton handleChange:", error);
      if (onError) onError(error);
    }
  };

  return (
    <>
      <button onClick={handleClick}>
        {buttonText || 'Browse'}
      </button>
      {/* Render the fallback file input only if not running in Electron */}
      {!isElectron && (
        <input
          ref={fileInputRef}
          type="file"
          multiple  // Allow selecting multiple files
          style={{ display: 'none' }}
          onChange={handleChange}
        />
      )}
    </>
  );
};

FolderBrowseButton.propTypes = {
  onFolderSelect: PropTypes.func.isRequired,
  buttonText: PropTypes.string,
  onError: PropTypes.func, // Optional error callback
};

FolderBrowseButton.defaultProps = {
  buttonText: 'Browse',
  onError: null,
};

export default FolderBrowseButton;
