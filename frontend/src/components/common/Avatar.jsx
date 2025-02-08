// src/components/common/Avatar.jsx
import React from 'react';
import PropTypes from 'prop-types';

const Avatar = ({ src, alt, size, style, className }) => {
  return (
    <img
      src={src}
      alt={alt}
      width={size}
      height={size}
      style={{
        borderRadius: '50%',
        ...style,
      }}
      className={className}
    />
  );
};

Avatar.propTypes = {
  src: PropTypes.string.isRequired,
  alt: PropTypes.string,
  size: PropTypes.number,
  style: PropTypes.object,
  className: PropTypes.string,
};

Avatar.defaultProps = {
  alt: 'avatar',
  size: 40,
  style: {},
  className: '',
};

export default Avatar;
