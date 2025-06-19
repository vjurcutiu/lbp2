import React, { useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { NavigationProvider } from './NavigationContext';
import AppLayout from '../../components/AppLayout';

const RouteManager = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  let sanitizedConversationId = conversationId;
  if (conversationId === undefined || 
      (conversationId !== "new" && isNaN(Number(conversationId)))) {
    sanitizedConversationId = "new";
  }

  useEffect(() => {
    if (conversationId !== sanitizedConversationId) {
      navigate(`/chat/${sanitizedConversationId}`, { replace: true });
    }
  }, [conversationId, sanitizedConversationId, navigate]);

  return (
    <NavigationProvider>
      <AppLayout conversationId={sanitizedConversationId} />
    </NavigationProvider>
  );
};

export default RouteManager;
