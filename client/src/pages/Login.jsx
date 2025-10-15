import { FcGoogle } from 'react-icons/fc';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();

  const handleGoogleSignIn = () => {
    // TODO: Integrate Google OAuth flow
    navigate('/chat');
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
          className="mt-8 flex w-full items-center justify-center gap-3 rounded-xl bg-white px-6 py-3 text-sm font-medium text-slate-900 shadow-lg transition hover:bg-slate-200"
        >
          <FcGoogle className="text-xl" />
          Continue with Google
        </button>
      </div>
    </div>
  );
};

export default Login;
