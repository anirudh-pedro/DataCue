/**
 * Custom hook for managing chat session state and initialization.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import sessionManager from '../utils/sessionManager';
import { apiGet, apiPost } from '../lib/api';

/**
 * Hook to manage authentication and session state.
 * Handles Firebase auth, session validation, and session initialization.
 */
export function useAuthSession() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('sessionId'));
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const isInitializingRef = useRef(false);

  const sessionReady = Boolean(sessionId && currentUser && !isLoadingHistory);

  // Auth state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        navigate('/login', { replace: true });
        setCurrentUser(null);
        return;
      }

      if (!sessionManager.isSessionValid()) {
        sessionManager.clearSession();
        try {
          await signOut(auth);
        } catch (error) {
          console.error('Error signing out expired session:', error);
        }
        navigate('/login', { replace: true });
        setCurrentUser(null);
        return;
      }

      setCurrentUser(user);
      setIsCheckingSession(false);
    });

    return () => unsubscribe();
  }, [navigate]);

  // Create a new chat session
  const createNewSession = useCallback(async (user) => {
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
    return newSessionId;
  }, []);

  // Initialize or load session
  const initializeSession = useCallback(async (user, loadHistoryCallback) => {
    if (isInitializingRef.current) return null;
    
    isInitializingRef.current = true;
    setIsLoadingHistory(true);
    
    try {
      const storedSessionId = localStorage.getItem('sessionId') || localStorage.getItem('chatSessionId');
      const storedUserId = localStorage.getItem('sessionUserId') || localStorage.getItem('chatSessionUserId');

      if (storedSessionId && storedUserId === user.uid) {
        const loaded = await loadHistoryCallback(storedSessionId);
        if (loaded) {
          setSessionId(storedSessionId);
          localStorage.setItem('sessionId', storedSessionId);
          localStorage.setItem('sessionUserId', user.uid);
          return storedSessionId;
        }
      }

      return await createNewSession(user);
    } catch (error) {
      console.error('Failed to initialise chat session:', error);
      return null;
    } finally {
      setIsLoadingHistory(false);
      isInitializingRef.current = false;
    }
  }, [createNewSession]);

  // Clear session state
  const clearSession = useCallback(() => {
    setSessionId(null);
    setIsLoadingHistory(false);
    isInitializingRef.current = false;
  }, []);

  return {
    currentUser,
    sessionId,
    setSessionId,
    isLoadingHistory,
    isCheckingSession,
    sessionReady,
    createNewSession,
    initializeSession,
    clearSession,
  };
}

/**
 * Hook to monitor backend health status.
 */
export function useHealthCheck() {
  const [healthWarning, setHealthWarning] = useState('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiGet('/health', { auth: false });
        if (!response.ok) {
          setHealthWarning('⚠️ Backend service is experiencing issues');
          return;
        }
        const health = await response.json();
        if (health.status === 'degraded') {
          if (health.services?.mongodb === 'unreachable') {
            setHealthWarning('⚠️ Database connection lost - chat history may not save');
          } else {
            setHealthWarning('⚠️ Some services are degraded');
          }
        } else {
          setHealthWarning('');
        }
      } catch {
        setHealthWarning('⚠️ Unable to reach backend service');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return { healthWarning };
}

export default useAuthSession;
