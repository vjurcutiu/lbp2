import React from 'react';

const DeleteModal = ({ onClose, onConfirm }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white p-4 rounded shadow-lg w-[300px]">
        <h3 className="mb-2 text-lg font-semibold">Delete Conversation</h3>
        <p className="mb-4">Are you sure you want to delete this conversation?</p>
        <div className="flex justify-end">
          <button className="px-3 py-1 mr-2 bg-gray-300 rounded" onClick={onClose}>
            Cancel
          </button>
          <button className="px-3 py-1 bg-red-500 text-white rounded" onClick={onConfirm}>
            Yes, Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;
