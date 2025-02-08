import React, { useState } from 'react';
import ChatWindow from './ChatWindow';

const App = () => {
  // Example conversation state.
  const [messages, setMessages] = useState([
    { sender: 'user', text: 'Hello!' },
    { sender: 'ai', text: 'Hi there! How can I help you today?' },
  ]);

  return (
    <div>
      <h1>Chat App</h1>
      <ChatWindow messages={messages} />
    </div>
  );
};

export default App;
