// src/components/common/ConversationSidebar.jsx
import React from 'react';
import PropTypes from 'prop-types';
import FolderBrowseButton from './FolderBrowseButton'; // Import the folder browse button

const ConversationSidebar = ({ conversations, onSelect, activeConversationId, onFolderImport }) => {
  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <h2 style={styles.title}>Conversations</h2>
        {/* Add the Folder Browse Button here */}
        <FolderBrowseButton onFolderSelect={onFolderImport} buttonText="Import Files" />
      </div>
      <ul style={styles.list}>
        {conversations.map((conv) => (
          <li
            key={conv.id}
            style={{
              ...styles.listItem,
              backgroundColor: conv.id === activeConversationId ? '#e0e0e0' : 'transparent',
            }}
            onClick={() => onSelect(conv.id)}
          >
            {conv.title || `Conversation ${conv.id}`}
          </li>
        ))}
      </ul>
    </div>
  );
};

const styles = {
  sidebar: {
    width: '250px',
    borderRight: '1px solid #ccc',
    padding: '15px',
    backgroundColor: '#f9f9f9',
    overflowY: 'auto',
    height: '100%',
  },
  header: {
    marginBottom: '15px',
  },
  title: {
    margin: '0 0 10px 0',
    fontSize: '18px',
  },
  list: {
    listStyleType: 'none',
    padding: 0,
    margin: 0,
  },
  listItem: {
    padding: '10px',
    marginBottom: '5px',
    cursor: 'pointer',
    borderRadius: '4px',
  },
};

ConversationSidebar.propTypes = {
  conversations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string,
    })
  ).isRequired,
  onSelect: PropTypes.func.isRequired,
  activeConversationId: PropTypes.number,
  onFolderImport: PropTypes.func.isRequired, // Callback for folder import
};

ConversationSidebar.defaultProps = {
  activeConversationId: null,
};

export default ConversationSidebar;
