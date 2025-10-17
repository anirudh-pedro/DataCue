import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import Navbar from '../components/Navbar';

const Profile = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      const otpVerified = sessionStorage.getItem('otpVerified') === 'true';

      if (!currentUser) {
        navigate('/login', { replace: true });
        return;
      }

      if (!otpVerified) {
        if (currentUser.email) {
          sessionStorage.setItem('otpEmail', currentUser.email);
        }
        navigate('/verify-otp', { replace: true, state: { email: currentUser.email } });
        return;
      }

      setUser(currentUser);
    });

    return unsubscribe;
  }, [navigate]);

  const handleSignOut = async () => {
    await signOut(auth);
    window.location.href = '/login';
  };

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-[#0d1117] text-white">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-slate-400">Loading profile…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#0d1117] text-white">
      <Navbar />
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-xl rounded-3xl border border-slate-800 bg-slate-900/80 p-10 shadow-2xl shadow-black/40">
          <div className="flex flex-col items-center gap-4 text-center">
            <img
              src={user.photoURL || '/logo.png'}
              alt={user.displayName || 'User avatar'}
              className="h-20 w-20 rounded-full border border-slate-700 object-cover"
              referrerPolicy="no-referrer"
              loading="lazy"
              onError={(event) => {
                event.currentTarget.onerror = null;
                event.currentTarget.src = '/logo.png';
              }}
            />
            <div>
              <h1 className="text-xl font-semibold">
                {user.displayName || 'Unnamed User'}
              </h1>
              <p className="mt-1 text-sm text-slate-300">{user.email}</p>
            </div>
            <div className="mt-6 grid w-full grid-cols-1 gap-4 text-left">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">Email Status</p>
                <p className="mt-2 text-sm font-medium text-white">{user.emailVerified ? 'Verified' : 'Pending verification'}</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">Last Login</p>
                <p className="mt-2 text-sm font-medium text-white">
                  {user.metadata?.lastSignInTime || '—'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleSignOut}
              className="mt-6 w-full rounded-xl border border-rose-500/40 bg-rose-500/20 px-6 py-3 text-sm font-semibold text-rose-200 transition hover:border-rose-400 hover:bg-rose-500/30"
            >
              Sign out of DataCue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
