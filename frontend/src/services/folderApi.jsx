// folderApi.jsx

import apiClient from './apiClient';
// IMPORTANT: import your singleton or context instance of UploadTrackingService!
import uploadTrackingService from '../features/uploadTracking/uploadTrackingService'; // Adjust path as needed


/**
 * Starts a folder processing job and connects to the WebSocket for progress.
 * @param {string|string[]} folderPath - Path(s) to process.
 * @param {string|string[]} extension - Extension(s) to process.
 * @param {object} [options] - { store: Redux store instance (optional, only if not singleton service) }
 * @returns {Promise<string>} - Resolves to the sessionId for this upload.
 */
export const processFolder = async (folderPath, extension, options = {}) => {
  // 1) Kick off the job and get a session ID
  const folderPaths = Array.isArray(folderPath) ? folderPath : [folderPath];
  const extensions = Array.isArray(extension) ? extension : [extension || ".txt"];
  const response = await apiClient.post('/files/process_folder', {
    folder_paths: folderPaths,
    extensions: extensions,
  });
  const { sessionId } = response;
  if (!sessionId) throw new Error('Missing session ID in response.');

  // 2) Connect to the WebSocket for real-time progress tracking
  // If using a global service (preferred), just call connect:
  uploadTrackingService.connect(sessionId);

  // If you need to use a store-aware instance (less common), you could do:
  // if (options.store) {
  //   const tempService = new UploadTrackingService(options.store);
  //   tempService.connect(sessionId);
  // }

  // 3) Return sessionId for use in your UI (e.g., to trigger modal, etc.)
  return sessionId;
};

/**
 * Cancels a processing session.
 * @param {string} sessionId
 * @returns {Promise<void>}
 */
export const cancelProcessFolder = async (sessionId) => {
  if (!sessionId) throw new Error('No sessionId provided');
  await apiClient.post('/files/process_folder/cancel', {
    session_id: sessionId
  });
};
