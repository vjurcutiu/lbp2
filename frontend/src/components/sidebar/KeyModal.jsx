import React, { useState } from 'react';
import AbstractModal from '../common/AbstractModal';
import { updatePineconeKey, updateOpenAIKey } from '../../services/apiVaultService';

/**
 * KeyModal Component
 * 
 * Props:
 * - isOpen: boolean - controls visibility
 * - onClose: () => void - callback to close modal
 */
export default function KeyModal({ isOpen, onClose }) {
  const [pineconeKey, setPineconeKey] = useState('');
  const [openAiKey, setOpenAiKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await updatePineconeKey(pineconeKey);
      await updateOpenAIKey(openAiKey);
      onClose();
    } catch (err) {
      console.error(err);
      setError('Failed to update keys. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const actions = [
    { label: 'Cancel', onClick: onClose, variant: 'secondary' },
    { label: isSubmitting ? 'Saving...' : 'Save', onClick: handleSave, variant: 'primary' }
  ];

  return (
    <AbstractModal title="Configure API Keys" onClose={onClose} actions={actions}>
      <div className="space-y-4">
        <div>
          <label htmlFor="pinecone-key" className="block text-sm font-medium text-gray-700">
            Pinecone API Key
          </label>
          <input
            id="pinecone-key"
            type="password"
            value={pineconeKey}
            onChange={(e) => setPineconeKey(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md p-2"
            placeholder="Enter Pinecone API Key"
          />
        </div>
        <div>
          <label htmlFor="openai-key" className="block text-sm font-medium text-gray-700">
            OpenAI API Key
          </label>
          <input
            id="openai-key"
            type="password"
            value={openAiKey}
            onChange={(e) => setOpenAiKey(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md p-2"
            placeholder="Enter OpenAI API Key"
          />
        </div>
        {error && (
          <p className="text-sm text-red-500">{error}</p>
        )}
      </div>
    </AbstractModal>
  );
}
