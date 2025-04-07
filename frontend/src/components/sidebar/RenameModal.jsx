import React from 'react';

const RenameModal = ({ newTitle, setNewTitle, onClose, onSave }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-opacity-25"
    onClick={onClose}>
      <div className="bg-white p-4 rounded shadow-lg w-[300px]"
        onClick={(e) => e.stopPropagation()}>
        <h3 className="mb-2 text-lg font-semibold">Rename Conversation</h3>
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          className="border border-gray-300 p-2 mb-4 w-full"
        />
        <div className="flex justify-end">
          <button className="px-3 py-1 mr-2 bg-gray-300 rounded" onClick={onClose}>
            Cancel
          </button>
          <button className="px-3 py-1 bg-gray-500 rounded" onClick={onSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default RenameModal;
