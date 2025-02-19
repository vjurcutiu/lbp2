// src/components/common/ChatHeader.jsx
import React from 'react';
import PropTypes from 'prop-types';

const ChatHeader = ({ title, onBack, style, className }) => {
  return (
    <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '10px 15px',
      backgroundColor: '#f2f2f2',
      width: '100%',
      boxShadow: '0 2px 1px rgba(0, 0, 0, 0.1)',
      marginBottom: '1px',  
      ...style,
    }}
      className={className}
    >
      {onBack && (
        <button onClick={onBack} style={{ marginRight: '10px' }}>
          Back
        </button>
      )}
      <h2 style={{ margin: 0, fontSize: '18px' }}>{title}</h2>
    </div>
  );
};

ChatHeader.propTypes = {
  title: PropTypes.string.isRequired,
  onBack: PropTypes.func,
  style: PropTypes.object,
  className: PropTypes.string,
};

ChatHeader.defaultProps = {
  onBack: null,
  style: {},
  className: '',
};

export default ChatHeader;
