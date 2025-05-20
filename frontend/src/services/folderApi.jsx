// folderApi.jsx

import apiClient, { createSSEConnection } from './apiClient';

export const processFolder = async (folderPath, extension, onProgress) => {
  // 1) Kick off the job and get a session ID
  const { sessionId } = await apiClient.post('/files/process_folder', {
    folder_paths: folderPath,
    extensions: extension || ".txt"
  });
  if (!sessionId) throw new Error('Missing session ID in response.');

  // 2) Open the SSE connection for progress updates
  const eventSource = createSSEConnection(
    `/files/process_folder?session_id=${sessionId}`
  );

  // 3) Listen for progress events
  eventSource.addEventListener('progress', (e) => {
    const parsed = JSON.parse(e.data);
    const value = parsed.data.value;
    onProgress(value);
  });

  // 4) Wrap the final “complete” and any SSE error into a promise
  const resultPromise = new Promise((resolve, reject) => {
    eventSource.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data);
      if (data.error) {
        // e.g. “Processing cancelled by user”
        reject(new Error(data.error));
      } else {
        resolve(data);
      }
      eventSource.close();
    });

    eventSource.addEventListener('error', (err) => {
      const msg = err?.message || 'Unknown SSE error';
      reject(new Error(`SSE Error: ${msg}`));
      eventSource.close();
    });
  });

  // 5) Return the session ID, the EventSource, and the promise for final results
  return { sessionId, eventSource, resultPromise };
};

// —————————————————————————————————————————————
// New helper: cancel an in‑flight processing session
export const cancelProcessFolder = async (sessionId) => {
  if (!sessionId) throw new Error('No sessionId provided');
  await apiClient.post('/files/process_folder/cancel', {
    session_id: sessionId
  });
};
