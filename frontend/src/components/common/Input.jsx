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
      style={style}
      className={`px-3 py-2 border border-gray-300 rounded text-base focus:outline-none focus:ring focus:border-blue-300 dark:bg-gray-800 dark:text-white ${className}`}
      {...rest}
    />
  );
};

Input.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  style: PropTypes.object,
  className: PropTypes.string,
};

Input.defaultProps = {
  placeholder: '',
  style: {},
  className: '',
};

export default Input;
