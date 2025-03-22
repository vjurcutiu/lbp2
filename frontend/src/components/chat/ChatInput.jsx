import React from 'react';
import PropTypes from 'prop-types';
import Button from '../common/Button';
import Input from '../common/Input';

const ChatInput = ({ value, onChange, onSend, placeholder, disabled }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled) {
        onSend(value);
      }
    }
  };

  return (
    <div className="flex items-center w-full p-1 bg-gray-200 dark:bg-gray-700">
      <Input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        onKeyPress={handleKeyPress}
        disabled={disabled}
        className="flex-1 mr-2"
      />
      <Button
        onClick={() => !disabled && onSend(value)}
        className="bg-gray-200 dark:bg-gray-700"
        disabled={disabled}
      >
        Send
      </Button>
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
