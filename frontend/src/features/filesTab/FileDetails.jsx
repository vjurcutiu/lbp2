import React from 'react';

const FileDetails = ({ file }) => (
  <div style={{
    background: '#e6e9ef',
    borderRadius: '1rem',
    padding: '2rem 1rem',
    minWidth: '220px',
    maxWidth: '220px',
    height: '100%',
    boxShadow: '2px 0 8px rgba(0,0,0,0.05)'
  }}>
    {file ? (
      <>
        <h4>{file.name}</h4>
        <p><b>Type:</b> {file.type}</p>
        <p><b>Size:</b> {file.size}</p>
        <p><b>Uploaded:</b> {file.uploaded}</p>
      </>
    ) : (
      <p style={{ color: '#777' }}>Select a file to see details.</p>
    )}
  </div>
);

export default FileDetails;