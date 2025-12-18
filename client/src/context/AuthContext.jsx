/**
 * Auth Context - Global authentication state management
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import sessionManager from '../utils/sessionManager';

const AuthContext = createContext(null);

// Flag to indicate OTP flow is in progress - don't auto-signout during this
let otpFlowInProgress = false;

export function setOtpFlowInProgress(value) {
  otpFlowInProgress = value;
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      try {
        if (user) {
          // Skip auto-signout if OTP flow is in progress
          if (otpFlowInProgress) {
            setCurrentUser(user);
            setIsLoading(false);
            return;
          }
          
          // Validate session
          if (!sessionManager.isSessionValid()) {
            sessionManager.clearSession();
            await signOut(auth);
            setCurrentUser(null);
          } else {
            setCurrentUser(user);
          }
        } else {
          setCurrentUser(null);
        }
      } catch (err) {
        console.error('Auth state change error:', err);
        setError(err.message);
        setCurrentUser(null);
      } finally {
        setIsLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const logout = async () => {
    try {
      sessionManager.clearSession();
      await signOut(auth);
      setCurrentUser(null);
    } catch (err) {
      console.error('Logout error:', err);
      throw err;
    }
  };

  const value = {
    currentUser,
    isLoading,
    error,
    isAuthenticated: !!currentUser,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
