import apiClient, { createSSEConnection } from './apiClient';

export const processFolder = async (folderPath, extension = ".txt", onProgress) => {
  try {
    // Step 1: Call the POST endpoint to start processing.
    const response = await apiClient.post('/files/process_folder', {
      folder_path: folderPath,
      extension: extension || ".txt"
    });

    // Since the response interceptor returns response.data directly,
    // we destructure sessionId directly from response.
    const { sessionId } = response;
    if (!sessionId) {
      throw new Error('Missing session ID in response.');
    }

    // Step 2: Open the SSE connection with the session id as a query parameter.
    const eventSource = createSSEConnection(`/files/process_folder?session_id=${sessionId}`);

    // Listen for progress updates.
    eventSource.addEventListener('progress', (event) => {
      console.log(event.data);
      const data = JSON.parse(event.data);
      onProgress(data.value);
    });

    // Listen for the completion event.
    return new Promise((resolve, reject) => {
      eventSource.addEventListener('complete', (event) => {
        resolve(JSON.parse(event.data));
        eventSource.close();
      });

      eventSource.addEventListener('error', (error) => {
        const errMsg = error && error.message ? error.message : "Unknown SSE error";
        reject(new Error(`SSE Error: ${errMsg}`));
        eventSource.close();
      });
    });
  } catch (error) {
    throw error.response?.data || error;
  }
};
