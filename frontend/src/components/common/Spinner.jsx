// src/components/common/Spinner.jsx
import React from 'react';

const Spinner = ({ size, color, style }) => {
  return (
    <div style={{ ...spinnerStyle, width: size, height: size, borderColor: color, ...style }}>
      {/* Simple CSS spinner */}
    </div>
  );
};

const spinnerStyle = {
  border: '4px solid #f3f3f3',
  borderTop: '4px solid #3498db',
  borderRadius: '50%',
  animation: 'spin 2s linear infinite',
};

export default Spinner;
