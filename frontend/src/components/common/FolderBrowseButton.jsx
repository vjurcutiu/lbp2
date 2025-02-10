// src/components/common/FolderBrowseButton.jsx
import React, { useRef } from 'react';
import PropTypes from 'prop-types';

/**
 * FolderBrowseButton renders a button that, when clicked,
 * opens a file dialog that allows the user to select a folder.
 * 
 * In a standard browser, the file input with the "webkitdirectory" attribute
 * will return a FileList with relative paths. This component extracts the first
 * folder name (as an approximation) and passes it to the onFolderSelect callback.
 * 
 * In an Electron (or similar) environment, you might replace this implementation
 * with one that uses native file dialogs to obtain an absolute folder path.
 */
const FolderBrowseButton = ({ onFolderSelect, buttonText, onError }) => {
  const fileInputRef = useRef(null);

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    } else {
      const error = new Error("File input element not found.");
      console.error(error);
      if (onError) onError(error);
    }
  };

  const handleChange = async (e) => {
    try {
      const files = e.target.files;
      if (!files || files.length === 0) {
        throw new Error("No files selected.");
      }
      const firstFile = files[0];
      if (!firstFile) {
        throw new Error("No file data available.");
      }

      let folderPath;
      if (window.electronAPI) {
        // In Electron, use the native dialog to get the full folder path.
        folderPath = await window.electronAPI.selectFolder();
      } else {
        // In a browser, we can only use the relative path.
        const relativePath = firstFile.webkitRelativePath || '';
        if (!relativePath) {
          throw new Error("Could not determine folder from file path.");
        }
        // Extract the first segment as the folder name.
        folderPath = relativePath.split('/')[0];
      }

      if (!folderPath) {
        throw new Error("Folder name is empty.");
      }

      onFolderSelect(folderPath);
    } catch (error) {
      console.error("Error in FolderBrowseButton handleChange:", error);
      if (onError) {
        onError(error);
      }
    }
  };

  return (
    <>
      <button onClick={handleClick}>
        {buttonText || 'Browse'}
      </button>
      {/* The input is hidden and uses the "webkitdirectory" attribute for folder selection */}
      <input
        ref={fileInputRef}
        type="file"
        webkitdirectory="true"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
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
