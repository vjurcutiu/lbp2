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
        backgroundColor: '#007bff',
        color: '#fff',
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
