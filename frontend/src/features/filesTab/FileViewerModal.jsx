import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchFileContent } from './services/fileFetch';

const FileViewerModal = ({ filePath, onClose }) => {
  const [content, setContent] = useState('Loading...');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!filePath) return;
    fetchFileContent(filePath)
      .then(setContent)
      .catch(err => {
        setError(err.message);
        setContent('');
      });
  }, [filePath]);

  return (
    <div style={{
      position: 'fixed',
      top: '5%',
      left: '10%',
      width: '80%',
      height: '90%',
      background: '#fff',
      borderRadius: '1rem',
      boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <div style={{ padding: '1rem', borderBottom: '1px solid #ccc' }}>
        <button onClick={onClose} style={{ float: 'right' }}>✖</button>
        <h3>Viewing: {filePath.split(/[\\/]/).pop()}</h3>
      </div>
      <div style={{
        padding: '1rem',
        overflowY: 'auto',
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        flex: 1
      }}>
        {error ? <div style={{ color: 'red' }}>{error}</div> : content}
      </div>
    </div>
  );
};

FileViewerModal.propTypes = {
  filePath: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default FileViewerModal;
