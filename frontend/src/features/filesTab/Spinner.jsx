import React from 'react';

const Spinner = () => (
  <span style={{
    display: 'inline-block',
    width: '18px',
    height: '18px',
    border: '3px solid #bbb',
    borderTop: '3px solid #3498db',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  }} />
);

// Spinner keyframes (ensure this is only added once)
if (typeof window !== "undefined" && !document.getElementById("global-spinner-keyframes")) {
  const style = document.createElement("style");
  style.id = "global-spinner-keyframes";
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

export default Spinner;