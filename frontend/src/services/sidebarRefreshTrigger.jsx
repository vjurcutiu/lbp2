import { useEffect } from 'react';
import PropTypes from 'prop-types';

const SidebarRefreshTrigger = ({ refreshSidebar }) => {
  useEffect(() => {
    // When this component mounts, trigger the sidebar refresh.
    refreshSidebar();
  }, [refreshSidebar]);

  return null; // This component does not render any visible UI.
};

SidebarRefreshTrigger.propTypes = {
  refreshSidebar: PropTypes.func.isRequired,
};

export default SidebarRefreshTrigger;
