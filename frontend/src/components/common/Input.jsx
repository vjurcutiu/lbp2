// src/components/common/Input.jsx
import React from 'react';
import PropTypes from 'prop-types';

const Input = ({ value, onChange, placeholder, style, className, ...rest }) => {
  return (
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{
        padding: '8px 12px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        fontSize: '16px',
        outline: 'none',
        ...style,
      }}
      className={className}
      {...rest}
    />
  );
};

Input.propTypes = {
  value: PropTypes.string.isRequired,      // The current value of the input
  onChange: PropTypes.func.isRequired,       // Function to handle changes (receives the event)
  placeholder: PropTypes.string,             // Placeholder text to display when input is empty
  style: PropTypes.object,                   // Additional inline styles
  className: PropTypes.string,               // Additional CSS class names
};

Input.defaultProps = {
  placeholder: '',
  style: {},
  className: '',
};

export default Input;
