import { describe, test, beforeEach, expect, vi } from 'vitest';
import {
  addConversationListListener,
  removeConversationListListener,
  addNewConversationListener,
  removeNewConversationListener,
} from '../src/services/listeners/socketListeners';

// Mock the underlying socket module using Vitest's mocking API
vi.mock('../src/services/websocket/socket', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
  },
}));

// Import the mocked socket module
import socket from '../src/services/websocket/socket';

describe('socketListeners', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('addConversationListListener registers the "conversation_list" event', () => {
    const callback = vi.fn();
    addConversationListListener(callback);
    expect(socket.on).toHaveBeenCalledWith("conversation_list", callback);
  });

  test('removeConversationListListener removes the "conversation_list" event', () => {
    const callback = vi.fn();
    removeConversationListListener(callback);
    expect(socket.off).toHaveBeenCalledWith("conversation_list", callback);
  });

  test('addNewConversationListener registers the "new_conversation" event', () => {
    const callback = vi.fn();
    addNewConversationListener(callback);
    expect(socket.on).toHaveBeenCalledWith("new_conversation", callback);
  });

  test('removeNewConversationListener removes the "new_conversation" event', () => {
    const callback = vi.fn();
    removeNewConversationListener(callback);
    expect(socket.off).toHaveBeenCalledWith("new_conversation", callback);
  });
});
