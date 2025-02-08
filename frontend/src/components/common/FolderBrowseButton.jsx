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
const FolderBrowseButton = ({ onFolderSelect, buttonText }) => {
  const fileInputRef = useRef(null);

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      // In browsers using the "webkitdirectory" attribute,
      // each file has a `webkitRelativePath` property like "FolderName/subfolder/file.txt".
      // We can extract the top-level folder name from the first file.
      const firstFile = files[0];
      const relativePath = firstFile.webkitRelativePath || '';
      const folderName = relativePath.split('/')[0]; // This is our best guess of the folder name

      // Pass the folder name (or an array of files, if needed) to the callback.
      onFolderSelect(folderName);
    }
  };

  return (
    <>
      <button onClick={handleClick}>
        {buttonText || 'Browse'}
      </button>
      {/* The input is hidden and has the attribute "webkitdirectory" to enable folder selection */}
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
};

FolderBrowseButton.defaultProps = {
  buttonText: 'Browse',
};

export default FolderBrowseButton;
