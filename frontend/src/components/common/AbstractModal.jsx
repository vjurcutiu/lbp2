import React from 'react';

/**
 * AbstractModal Component
 * 
 * Props:
 * - title: string - modal title
 * - children: React.ReactNode - modal content
 * - onClose: () => void - callback to close the modal
 * - actions: { label: string; onClick: () => void; variant?: 'primary' | 'secondary' }[] - action buttons
 */
const AbstractModal = ({ title, children, onClose, actions }) => {
  return (
    <div
      className="fixed inset-0 flex items-center justify-center bg-opacity-25"
      onClick={onClose}
    >
      <div
        className="bg-white p-6 rounded-2xl shadow-lg w-[300px]"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-4 text-xl font-semibold">{title}</h3>
        <div className="mb-6">
          {children}
        </div>
        <div className="flex justify-end space-x-2">
          {actions.map((action, idx) => (
            <button
              key={idx}
              onClick={action.onClick}
              className={`px-4 py-2 rounded-lg ${
                action.variant === 'primary'
                  ? 'bg-gray-500 text-gray-700'
                  : 'bg-gray-500 text-gray-700'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AbstractModal;
