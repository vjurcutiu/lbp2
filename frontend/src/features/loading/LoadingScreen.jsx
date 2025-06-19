import React from 'react';

const LoadingScreen = () => (
  <div style={{
    width: '100vw',
    height: '100vh',
    background: '#1a1a1a',
    color: '#fff',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center'
  }}>
    <div className="spinner" style={{
      border: '8px solid #f3f3f3',
      borderTop: '8px solid #3498db',
      borderRadius: '50%',
      width: 60,
      height: 60,
      animation: 'spin 1s linear infinite'
    }} />
    <h2 style={{ marginTop: 24 }}>Connecting…</h2>
    <style>
      {`
        @keyframes spin {
          0% { transform: rotate(0deg);}
          100% { transform: rotate(360deg);}
        }
      `}
    </style>
  </div>
);

export default LoadingScreen;
