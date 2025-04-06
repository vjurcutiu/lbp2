import React, { useState } from 'react';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import NewChat from './NewChat';
import { useChatService } from '../../services/conversations/useChatService';

const ChatMetaContainer = ({ conversationId, messages, updateMessages, onNewMessage }) => {
  const [input, setInput] = useState('');

  // Use the custom hook for sending messages.
  const { handleSend, isWaiting } = useChatService({ conversationId, onNewMessage, updateMessages });

  const onSend = async (inputText) => {
    await handleSend(inputText);
    setInput('');
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-100 dark:bg-gray-800">
      <ChatHeader title="Chat App" />
      {messages.length > 0 ? (
        <ChatWindow messages={messages} />
      ) : (
        <NewChat messages={messages} />
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
