// src/components/FolderProcessor.jsx
import React from 'react';
import FolderBrowseButton from './common/FolderBrowseButton';
import { processFolder } from '../services'; // Adjust the import path if needed

const FolderProcessor = () => {
  // This function will be passed as the onFolderSelect callback.
  // It receives the selected file/folder paths from FolderBrowseButton.
  const handleFolderSelect = async (selectedPaths) => {
    try {
      // Call your API function with the file data.
      const response = await processFolder(selectedPaths);
      console.log('Folder processed successfully:', response);
      // You can now update state, show a notification, etc.
    } catch (error) {
      console.error('Error processing folder:', error);
      // Optionally, show an error message to the user.
    }
  };

  return (
    <div>
      <h1>Process Folder</h1>
      <FolderBrowseButton 
        onFolderSelect={handleFolderSelect} 
        buttonText="Select Folder" 
        onError={(error) => console.error('Selection error:', error)}
      />
    </div>
  );
};

export default FolderProcessor;
