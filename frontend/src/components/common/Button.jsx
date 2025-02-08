// Button.jsx
import React from 'react';
import PropTypes from 'prop-types';

const Button = ({ children, onClick, style, className, disabled, ...rest }) => {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '10px 15px',
        border: 'none',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        ...style,
      }}
      className={className}
      disabled={disabled}
      {...rest}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  style: PropTypes.object,
  className: PropTypes.string,
  disabled: PropTypes.bool,
};

Button.defaultProps = {
  onClick: () => {},
  style: {},
  className: '',
  disabled: false,
};

export default Button;
