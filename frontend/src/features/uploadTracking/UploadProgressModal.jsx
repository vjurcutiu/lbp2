import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  uploadStarted,
  fileUploaded,
  fileFailed,
  uploadComplete,
  resetUpload,
} from './uploadTrackingSlice';

const UploadProgressModal = ({ onCancel }) => {
  const {
    totalFiles,
    uploadedCount,
    uploadedFiles,
    failedFiles,
    isComplete,
  } = useSelector((state) => state.uploadTracking);

  console.log('UploadProgressModal render with state:', {
    totalFiles,
    uploadedCount,
    uploadedFiles,
    failedFiles,
    isComplete,
  });

  const dispatch = useDispatch();

  const handleClose = () => {
    dispatch(resetUpload());
    if (onCancel) onCancel();
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/25">
      <div className="bg-white p-6 rounded-lg shadow-xl w-96 max-h-[70vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">
          {isComplete
            ? 'Upload Completed!'
            : `Files uploaded ${uploadedCount}/${totalFiles}`}
        </h3>

        <div className="mb-4">
          <h4 className="font-semibold">Uploaded Files:</h4>
          <ul className="list-disc list-inside max-h-40 overflow-y-auto border p-2 rounded">
            {uploadedFiles.map((fileName, index) => (
              <li key={index}>{fileName}</li>
            ))}
          </ul>
        </div>

        {failedFiles.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold text-red-600">Failed Files:</h4>
            <ul className="list-disc list-inside max-h-40 overflow-y-auto border p-2 rounded text-red-600">
              {failedFiles.map(({ fileName, error }, index) => (
                <li key={index}>
                  {fileName}: {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {!isComplete && (
          <button
            className="mt-4 px-4 py-2 !bg-red-500 text-white rounded hover:!bg-red-600 transition-colors"
            onClick={handleClose}
          >
            Cancel Upload
          </button>
        )}

        {isComplete && (
          <button
            className="mt-4 px-4 py-2 !bg-blue-600 text-white rounded hover:!bg-blue-700 transition-colors"
            onClick={handleClose}
          >
            Close
          </button>
        )}
      </div>
    </div>
  );
};

export default UploadProgressModal;
