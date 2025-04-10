import apiClient, { createSSEConnection } from './apiClient';

export const processFolder = async (folderPath, extension = ".txt", onProgress) => {
  try {
    // First create processing session via API client
    // Create SSE connection first to listen for session ID
    const eventSource = createSSEConnection('/files/process_folder');
    
    // Send POST request with folder data
    await apiClient.post('/files/process_folder', {
      folder_path: folderPath,
      extension: extension || ".txt"
    });

    // Wait for session ID from SSE
    const sessionId = await new Promise((resolve, reject) => {
      eventSource.addEventListener('session', (event) => {
        const { sessionId } = JSON.parse(event.data);
        resolve(sessionId);
      });

      eventSource.addEventListener('error', (error) => {
        reject(new Error(`Session ID error: ${error.message}`));
      });
    });

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      onProgress(data.value);
    });

    return new Promise((resolve, reject) => {
      eventSource.addEventListener('complete', (event) => {
        resolve(JSON.parse(event.data));
        eventSource.close();
      });

      eventSource.addEventListener('error', (error) => {
        console.error("SSE error event received:", error); // Full object logging
        const errMsg = error && error.message ? error.message : "Unknown SSE error";
        reject(new Error(`SSE Error: ${errMsg}`));
        eventSource.close();
      });
    });
  } catch (error) {
    throw error.response?.data || error;
  }
};
