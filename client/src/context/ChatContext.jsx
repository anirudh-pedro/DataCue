/**
 * Chat Context - Global chat session and messages state management
 */

import { createContext, useContext, useState, useCallback } from 'react';
import { apiGet, apiPost, apiPatch } from '../lib/api';

const ChatContext = createContext(null);

// Helper functions
export const generateMessageId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2, 12);
};

export const buildTimestamp = () => 
  new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

export function ChatProvider({ children }) {
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('sessionId'));
  const [messages, setMessages] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [hasDashboard, setHasDashboard] = useState(false);

  // Create a new chat session
  const createSession = useCallback(async (user) => {
    const response = await apiPost('/chat/sessions', {
      user_id: user.uid,
      email: user.email,
      display_name: user.displayName,
    });

    if (!response.ok) {
      throw new Error('Failed to create chat session.');
    }

    const payload = await response.json();
    const newSessionId = payload.session_id;
    
    localStorage.setItem('sessionId', newSessionId);
    localStorage.setItem('sessionUserId', user.uid);
    setSessionId(newSessionId);
    setMessages([]);
    setHasDashboard(false);
    
    return newSessionId;
  }, []);

  // Load messages from backend
  const loadMessages = useCallback(async (targetSessionId) => {
    setIsLoadingHistory(true);
    try {
      const response = await apiGet(`/chat/sessions/${targetSessionId}/messages`);
      if (!response.ok) {
        throw new Error('Failed to load chat history.');
      }
      
      const payload = await response.json();
      const history = Array.isArray(payload.messages)
        ? payload.messages.map((msg) => ({
            id: msg.id || generateMessageId(),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            chart: msg.chart,
            metadata: msg.metadata || {},
            showDashboardButton: Boolean(msg.showDashboardButton),
          }))
        : [];

      setMessages(history);
      setHasDashboard(history.some((msg) => msg.showDashboardButton));
      
      return true;
    } catch (error) {
      console.error('Failed to load chat history:', error);
      clearSession();
      return false;
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Persist a message to backend
  const persistMessage = useCallback(async (message) => {
    if (!sessionId) return;

    try {
      await apiPost(`/chat/sessions/${sessionId}/messages`, {
        id: message.id,
        role: message.role,
        content: message.content,
        timestamp: message.timestamp,
        chart: message.chart,
        metadata: message.metadata,
        showDashboardButton: Boolean(message.showDashboardButton),
      });
    } catch (error) {
      console.error('Failed to persist message:', error);
    }
  }, [sessionId]);

  // Add a message to state and optionally persist
  const addMessage = useCallback((message, persist = true) => {
    const messageWithId = message.id ? message : { ...message, id: generateMessageId() };
    setMessages((prev) => [...prev, messageWithId]);
    
    if (persist) {
      persistMessage(messageWithId);
    }
    
    return messageWithId;
  }, [persistMessage]);

  // Update session title
  const updateTitle = useCallback(async (title) => {
    if (!sessionId) return;
    
    try {
      await apiPatch(`/chat/sessions/${sessionId}/title`, { title });
    } catch (error) {
      console.error('Failed to update title:', error);
    }
  }, [sessionId]);

  // Clear session state
  const clearSession = useCallback(() => {
    localStorage.removeItem('sessionId');
    localStorage.removeItem('sessionUserId');
    localStorage.removeItem('chatSessionId');
    localStorage.removeItem('chatSessionUserId');
    setSessionId(null);
    setMessages([]);
    setHasDashboard(false);
  }, []);

  // Switch to a different session
  const switchSession = useCallback(async (newSessionId) => {
    localStorage.setItem('sessionId', newSessionId);
    setSessionId(newSessionId);
    await loadMessages(newSessionId);
  }, [loadMessages]);

  const value = {
    sessionId,
    setSessionId,
    messages,
    setMessages,
    isLoadingHistory,
    hasDashboard,
    setHasDashboard,
    createSession,
    loadMessages,
    addMessage,
    persistMessage,
    updateTitle,
    clearSession,
    switchSession,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;
