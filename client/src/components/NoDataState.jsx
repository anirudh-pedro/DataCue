import { HiSparkles } from 'react-icons/hi2';
import { useNavigate } from 'react-router-dom';

const NoDataState = () => {
  const navigate = useNavigate();

  return (
    <div className="flex h-[60vh] flex-col items-center justify-center text-center">
      <HiSparkles className="mb-4 text-5xl text-slate-600" />
      <h2 className="text-xl font-semibold text-white">No visualizations yet</h2>
      <p className="mt-2 max-w-md text-sm text-slate-400">
        Upload a dataset from the chat experience to generate an interactive dashboard automatically.
      </p>
      <button
        onClick={() => navigate('/chat')}
        type="button"
        className="mt-6 rounded-xl bg-white px-5 py-2 text-sm font-medium text-[#0d1117] transition hover:bg-slate-200"
      >
        Upload a dataset
      </button>
    </div>
  );
};

export default NoDataState;
