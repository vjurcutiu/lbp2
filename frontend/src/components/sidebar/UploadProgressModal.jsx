import React from 'react';

const UploadProgressModal = ({ progress, onCancel }) => (
  <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
    <div className="bg-white p-6 rounded-lg shadow-xl w-96">
      <h3 className="text-lg font-semibold mb-4">Uploading Files ({progress}%)</h3>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div 
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
          style={{ width: `${progress}%` }}
        />
      </div>
      <button
        className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        onClick={onCancel}
      >
        Cancel Upload
      </button>
    </div>
  </div>
);

export default UploadProgressModal;
