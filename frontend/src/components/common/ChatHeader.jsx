// src/components/common/ChatHeader.jsx
import React from 'react';
import PropTypes from 'prop-types';
import DarkModeToggle from '../darkMode/DarkModeToggle';

const ChatHeader = ({ title, onBack, className }) => {
  return (
    <div className={`flex items-center justify-between p-2.5 bg-gray-200 dark:bg-gray-700 w-full shadow-sm mb-[1px] ${className}`}>
      <div className="flex items-center">
        {onBack && (
          <button onClick={onBack} className="mr-2.5">
            Back
          </button>
        )}
        <h2 className="m-0 text-lg">{title}</h2>
      </div>
      <DarkModeToggle />
    </div>
  );
};

ChatHeader.propTypes = {
  title: PropTypes.string.isRequired,
  onBack: PropTypes.func,
  className: PropTypes.string,
};

ChatHeader.defaultProps = {
  onBack: null,
  className: '',
};

export default ChatHeader;
