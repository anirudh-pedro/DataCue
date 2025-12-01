import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import sessionManager from '../utils/sessionManager';

const VerifyOtp = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(() => {
    return location.state?.email || sessionManager.getEmail() || '';
  });
  const [otp, setOtp] = useState('');
  const [statusMessage, setStatusMessage] = useState('An OTP has been sent to your email.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(300);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const emailServiceUrl = (import.meta.env.VITE_EMAIL_SERVICE_URL ?? 'http://localhost:4000').replace(/\/$/, '');

  useEffect(() => {
    // If accessing verify-otp without coming from login flow, redirect to login
    if (!location.state?.email && !sessionManager.getEmail()) {
      navigate('/login', { replace: true });
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        navigate('/login', { replace: true });
        return;
      }

      // Check if session is already valid
      if (sessionManager.isSessionValid()) {
        navigate('/chat', { replace: true });
        return;
      }

      if (!email && user.email) {
        setEmail(user.email);
      }
      
      setIsCheckingSession(false);
    });
    return unsubscribe;
  }, [email, navigate, location.state?.email]);

  useEffect(() => {
    if (!secondsRemaining) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => Math.max(prev - 1, 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [secondsRemaining]);

  const formattedTimer = () => {
    const minutes = Math.floor(secondsRemaining / 60);
    const seconds = secondsRemaining % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const resendOtp = async () => {
    if (!email) return;
    setIsSubmitting(true);
    setStatusMessage('Resending OTP…');
    try {
      const response = await fetch(`${emailServiceUrl}/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.message || 'Failed to resend OTP');
      }
      setStatusMessage('A new OTP has been sent to your email.');
      setSecondsRemaining(300);
    } catch (error) {
      console.error('Failed to resend OTP:', error);
      setStatusMessage('Failed to resend OTP. Please try again later.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!otp.trim()) {
      setStatusMessage('Please enter the verification code.');
      return;
    }

    setIsSubmitting(true);
    setStatusMessage('Verifying code…');
    try {
      const response = await fetch(`${emailServiceUrl}/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: otp.trim() }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.success) {
        throw new Error(payload.message || 'Invalid or expired code.');
      }

      // Create a new 4-day session
      sessionManager.createSession(email);
      
      // Show session info
      const sessionInfo = sessionManager.getSessionInfo();
      console.log('Session created, expires:', sessionInfo.expires);
      
      navigate('/chat', { replace: true });
    } catch (error) {
      console.error('OTP verification failed:', error);
      setStatusMessage(error.message || 'Failed to verify code.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    sessionManager.clearSession();
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Sign-out failed during OTP cancel:', error);
    }
    navigate('/login', { replace: true });
  };

  // Show loading state while checking session
  if (isCheckingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0d1117]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-white border-r-transparent"></div>
          <p className="mt-4 text-sm text-slate-400">Checking session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0d1117] px-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/80 p-10 text-center shadow-2xl shadow-black/40">
        <h1 className="text-2xl font-semibold text-white">Verify your email</h1>
        <p className="mt-3 text-sm text-slate-300">
          Enter the 6-digit code sent to
          <span className="ml-1 font-medium text-white">{email}</span>
        </p>
        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={otp}
            onChange={(event) => setOtp(event.target.value.replace(/[^0-9]/g, ''))}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-center text-lg font-semibold tracking-[0.6rem] text-white focus:border-slate-500 focus:outline-none"
            placeholder="••••••"
            autoFocus
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full rounded-xl px-4 py-3 text-sm font-semibold transition \
              ${isSubmitting ? 'bg-slate-700/70 text-slate-300 cursor-not-allowed' : 'bg-white text-slate-900 hover:bg-slate-200'}`}
          >
            {isSubmitting ? 'Verifying…' : 'Verify code'}
          </button>
          <button
            type="button"
            onClick={handleCancel}
            className="w-full rounded-xl border border-slate-700 bg-transparent px-4 py-3 text-sm font-semibold text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Cancel and go back
          </button>
        </form>
        <p className="mt-4 text-xs text-slate-400">{statusMessage}</p>
        <button
          type="button"
          onClick={resendOtp}
          disabled={isSubmitting || secondsRemaining > 0}
          className="mt-6 text-xs font-semibold text-sky-400 disabled:text-slate-600"
        >
          {secondsRemaining > 0 ? `Resend code in ${formattedTimer()}` : 'Resend code'}
        </button>
      </div>
    </div>
  );
};

export default VerifyOtp;
