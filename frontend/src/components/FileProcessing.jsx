// src/components/FileProcessing.jsx
import React, { useState } from 'react';
import FolderBrowseButton from './common/FolderBrowseButton';
import NotificationModal from './common/NotificationModal';
import { processFolder } from '../services/api'; // Your API function for the Flask route

const FileProcessing = () => {
  const [selectedFolder, setSelectedFolder] = useState('');
  const [notification, setNotification] = useState({
    visible: false,
    message: '',
  });

  const handleFolderSelect = (folderName) => {
    setSelectedFolder(folderName);
    // Call the API to process the folder.
    processFolder({ folder_path: folderName, extension: '.txt' })
      .then((res) => {
        // Customize your success message as needed.
        setNotification({
          visible: true,
          message: `Files imported successfully from "${folderName}".`,
        });
      })
      .catch((err) => {
        setNotification({
          visible: true,
          message: `File import failed for "${folderName}": ${err.message}`,
        });
      });
  };

  const closeNotification = () => {
    setNotification({ visible: false, message: '' });
  };

  return (
    <div>
      <h2>File Processing</h2>
      <FolderBrowseButton onFolderSelect={handleFolderSelect} buttonText="Select Folder" />
      {selectedFolder && <p>Selected Folder: {selectedFolder}</p>}
      <NotificationModal
        message={notification.message}
        visible={notification.visible}
        onClose={closeNotification}
      />
    </div>
  );
};

export default FileProcessing;
