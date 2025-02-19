// src/components/common/ChatInput.jsx
import React from 'react';
import PropTypes from 'prop-types';
import Button from './Button';
import Input from './Input';

const ChatInput = ({ value, onChange, onSend, placeholder, disabled }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend(value);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center',
      width: '100%',
      padding: '5px',
      backgroundColor: '#f2f2f2',
      }}>
      <Input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        onKeyPress={handleKeyPress}
        style={{ flex: 1, marginRight: '8px' }}
      />
      <Button 
        onClick={() => onSend(value)}
        style={{
          backgroundColor: '#f2f2f2',
          }}
        >Send</Button>
    </div>
  );
};

ChatInput.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onSend: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
};

ChatInput.defaultProps = {
  placeholder: 'Type a message...',
  disabled: false,
};

export default ChatInput;
