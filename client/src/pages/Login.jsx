import { useEffect, useState } from 'react';
import { FcGoogle } from 'react-icons/fc';
import { useNavigate } from 'react-router-dom';
import { GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult, onAuthStateChanged } from 'firebase/auth';
import { auth } from '../firebase';

const Login = () => {
  const navigate = useNavigate();
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const emailServiceUrl = import.meta.env.VITE_EMAIL_SERVICE_URL ?? 'http://localhost:4000';

  useEffect(() => {
    const handleRedirectResult = async () => {
      try {
        const result = await getRedirectResult(auth);
        if (result?.user?.email) {
          await proceedToOtp(result.user.email);
        }
      } catch (error) {
        console.error('Redirect sign-in failed:', error);
        setErrorMessage('Unable to sign in with Google. Please try again.');
      } finally {
        setIsSigningIn(false);
      }
    };

    handleRedirectResult();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (!user) {
        return;
      }

      const otpVerified = sessionStorage.getItem('otpVerified') === 'true';
      if (otpVerified) {
        navigate('/chat', { replace: true });
      } else {
        if (user.email) {
          sessionStorage.setItem('otpEmail', user.email);
        }
        navigate('/verify-otp', { replace: true, state: { email: user.email ?? sessionStorage.getItem('otpEmail') } });
      }
    });

    return () => unsubscribe();
  }, [navigate]);

  const sendOtp = async (email) => {
  const response = await fetch(`${emailServiceUrl.replace(/\/$/, '')}/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.message || 'Failed to send OTP');
    }
  };

  const proceedToOtp = async (email) => {
    try {
      await sendOtp(email);
      sessionStorage.setItem('otpEmail', email);
      sessionStorage.removeItem('otpVerified');
      navigate('/verify-otp', { replace: true, state: { email } });
    } catch (error) {
      console.error('OTP send failed:', error);
      setErrorMessage('Could not send OTP email. Please try again.');
    }
  };

  const handleGoogleSignIn = async () => {
    setErrorMessage('');
    setIsSigningIn(true);

    try {
      const isMobile = typeof window !== 'undefined' && window.innerWidth < 640;
      if (isMobile) {
        await signInWithRedirect(auth, new GoogleAuthProvider());
        return;
      } else {
        const result = await signInWithPopup(auth, new GoogleAuthProvider());
        if (result?.user?.email) {
          await proceedToOtp(result.user.email);
        }
      }
    } catch (error) {
      const code = error?.code || 'auth/error';
      if (code !== 'auth/popup-closed-by-user' && code !== 'auth/cancelled-popup-request') {
        setErrorMessage('Unable to sign in with Google. Please try again.');
      }
    } finally {
      setIsSigningIn(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0d1117] px-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/80 p-10 text-center shadow-2xl shadow-black/40">
        <img
          src="/logo.png"
          alt="DataCue Logo"
          className="mx-auto h-16 w-16 object-contain"
        />
        <h1 className="mt-6 text-2xl font-semibold text-white">Welcome to DataCue</h1>
        <p className="mt-2 text-sm text-slate-400">
          Sign in with Google to continue
        </p>
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={isSigningIn}
          className={`mt-8 flex w-full items-center justify-center gap-3 rounded-xl px-6 py-3 text-sm font-medium shadow-lg transition \
            ${isSigningIn ? 'bg-slate-300 text-slate-600 cursor-not-allowed' : 'bg-white text-slate-900 hover:bg-slate-200'}`}
        >
          <FcGoogle className="text-xl" />
          {isSigningIn ? 'Signing in…' : 'Continue with Google'}
        </button>
        {errorMessage ? (
          <p className="mt-4 text-xs text-rose-400">{errorMessage}</p>
        ) : null}
      </div>
    </div>
  );
};

export default Login;
