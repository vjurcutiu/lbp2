// folderApi.jsx

import apiClient from './apiClient';
// NO singleton import!


/**
 * Starts a folder processing job and returns the session ID.
 * @param {string|string[]} folderPath - Path(s) to process.
 * @param {string|string[]} extension - Extension(s) to process.
 * @returns {Promise<string>} - Resolves to the sessionId for this upload.
 */
export const processFolder = async (folderPath, extension) => {
  // 1) Kick off the job and get a session ID
  const folderPaths = Array.isArray(folderPath) ? folderPath : [folderPath];
  const extensions = Array.isArray(extension) ? extension : [extension || ".txt"];
  const response = await apiClient.post('/files/process_folder', {
    folder_paths: folderPaths,
    extensions: extensions,
  });
  const { sessionId } = response;
  if (!sessionId) throw new Error('Missing session ID in response.');
  // Just return the sessionId; do not connect the WS service here!
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
