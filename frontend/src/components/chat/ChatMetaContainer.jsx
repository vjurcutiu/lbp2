import React, { useState, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import NewChat from './NewChat';
import { useChatService } from '../../services/conversations/useChatService';

const ChatMetaContainer = ({ conversationId, messages, updateMessages, onNewMessage }) => {
  const [input, setInput] = useState('');
  const [showChatWindow, setShowChatWindow] = useState(false);

  useEffect(() => {
    if (!conversationId) setShowChatWindow(false);
  }, [conversationId]);

  // Use the custom hook for sending messages.
  const { handleSend, isWaiting } = useChatService({ conversationId, onNewMessage, updateMessages });

  const onSend = async (inputText) => {
    if (!showChatWindow) setShowChatWindow(true);
    await handleSend(inputText);
    setInput('');
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-100 dark:bg-gray-800">
      <ChatHeader title="Chat App" />
      {conversationId ? (
        <ChatWindow messages={messages} />
      ) : (
        <NewChat messages={messages} onNewMessage={onNewMessage} />
      )}
      <ChatInput
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={onSend}
        disabled={isWaiting}
      />
    </div>
  );
};

export default ChatMetaContainer;
