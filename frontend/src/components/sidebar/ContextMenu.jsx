import React from 'react';
import ReactDOM from 'react-dom';
import { FaEdit } from 'react-icons/fa';
import { MdDelete } from 'react-icons/md';

const ContextMenu = ({ x, y, conversation, onEdit, onDelete, onClose }) => {
  return ReactDOM.createPortal(
    <>
        <div className="fixed inset-0" onClick={onClose} />
        <div
            style={{ top: y, left: x }}
            className="fixed z-[10000] bg-white border border-gray-300 shadow-lg rounded"
            onClick={(e) => e.stopPropagation()}
        >
            <button
            className="flex items-center px-4 py-2 hover:bg-gray-100 w-full"
            onClick={() => { onEdit(conversation.id); onClose(); }}
            >
            <FaEdit className="mr-2" /> Edit
            </button>
            <button
            className="flex items-center px-4 py-2 hover:bg-gray-100 w-full"
            onClick={() => { onDelete(conversation.id); onClose(); }}
            >
            <MdDelete className="mr-2" /> Delete
            </button>
        </div>
        </>
,
    document.body
  );
};

export default ContextMenu;
