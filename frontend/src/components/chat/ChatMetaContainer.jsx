import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import NewChat from './NewChat';
import { useChatService } from '../../services/conversations/useChatService';

const ChatMetaContainer = ({ messages, updateMessages, onNewMessage }) => {
  const [input, setInput] = useState('');
  
  // Get conversationID from Redux; if not set, assume a "new" conversation.
  const activeConversationId = useSelector(
    (state) => state.conversations.activeConversationId
  );
  const conversationId = activeConversationId ? activeConversationId : "new";

  // Use the custom hook for sending messages.
  const { handleSend, isWaiting } = useChatService({
    conversationId,
    onNewMessage,
    updateMessages
  });

  const onSend = async (inputText) => {
    const messageToSend = inputText;
    setInput('');  // Clear input field immediately
    try {
      await handleSend(messageToSend);
    } catch (error) {
      console.error('Send failed:', error);
      // Optionally restore input or show error feedback
      // setInput(messageToSend);
    }
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
