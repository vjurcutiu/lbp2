import React, { createContext, useContext } from 'react';
import { useNavigate } from 'react-router-dom';

const NavigationContext = createContext(null);

export const NavigationProvider = ({ children }) => {
  const navigate = useNavigate();

  const setConversationId = (newConversationId) => {
    navigate(`/conversation/${newConversationId}`);
  };

  return (
    <NavigationContext.Provider value={{ setConversationId }}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigation = () => useContext(NavigationContext);
