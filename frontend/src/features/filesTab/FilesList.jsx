
import React from 'react';
import Spinner from './Spinner';

const FilesList = ({ files, selected, setSelected, onDoubleClick }) => (  
  <div style={{
    flex: 1,
    background: '#fff',
    borderRadius: '1rem',
    boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
    padding: '2rem',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column'
  }}>    
    <h3 style={{ marginBottom: '1.5rem' }}>Files</h3>
    {files.length > 0 ? (
      files.map(file => (
        <div
          key={file.id}
          onClick={() => setSelected(file)}
          onDoubleClick={() => onDoubleClick?.(file.file_path)}
          style={{
            padding: '1rem',
            borderRadius: '0.8rem',
            background: selected?.id === file.id ? '#dde5ff' : 'transparent',
            cursor: 'pointer',
            marginBottom: '0.7rem',
            transition: 'background 0.2s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span>{file.name}</span>
            {(file.status === 'pending' || file.status === 'uploading') && (
              <span style={{ marginLeft: '0.7rem' }}>
                <Spinner />
              </span>
            )}
            {file.status === 'error' && (
              <span style={{ color: 'red', marginLeft: '0.7rem' }}>
                &#9888; {file.error || 'Failed'}
              </span>
            )}
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              const confirmed = window.confirm(`Are you sure you want to delete "${file.name}"?`);
              if (confirmed) {
                file.onDelete?.(file.id);
              }
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#888',
              cursor: 'pointer',
              fontSize: '1.1rem',
            }}
            title="Remove file"
          >
            ✖
          </button>
        </div>
      ))
    ) : (
      <div style={{ color: '#888', fontStyle: 'italic' }}>No files found.</div>
    )}
  </div>
);

export default FilesList;
