import apiClient from './apiClient';

export const processFolder = async (folderPath, extension = ".txt") => {
  try {
    const response = await apiClient.post('/files/process_folder', {
      folder_path: folderPath,
      extension: extension
    });
    return response.data;
  } catch (error) {
    console.error('Folder processing error:', error);
    throw error;
  }
};
