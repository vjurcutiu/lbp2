// Button.jsx
import React from 'react';
import PropTypes from 'prop-types';

const Button = ({ children, onClick, className, disabled, ...rest }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded cursor-pointer ${
        disabled ? 'opacity-60 cursor-not-allowed' : ''
      } ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  className: PropTypes.string,
  disabled: PropTypes.bool,
};

Button.defaultProps = {
  onClick: () => {},
  className: '',
  disabled: false,
};

export default Button;
