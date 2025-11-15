import DashboardTile from './DashboardTile';

const formatNumber = (value, precision = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }

  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: precision,
    minimumFractionDigits: precision > 0 ? Math.min(precision, 2) : 0,
  }).format(value);
};

const KpiCard = ({ chart }) => {
  const { title = 'Key Metric', data = {}, config = {} } = chart;
  const precision = config.precision ?? 2;

  return (
    <DashboardTile title={title} className="bg-gradient-to-br from-indigo-950/40 via-slate-900/90 to-slate-900/60 border-indigo-900/30">
      <div className="flex w-full flex-col justify-center gap-6 text-white p-2">
        <div>
          <p className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            {formatNumber(data.primary_value, precision)}
          </p>
          <p className="mt-2 text-[11px] font-semibold uppercase tracking-widest text-indigo-300/70">
            Total Value
          </p>
        </div>
        <div className="grid grid-cols-3 gap-5 rounded-xl border border-slate-800/50 bg-slate-950/40 p-4 text-xs">
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Avg</p>
            <p className="mt-2 text-lg font-semibold text-emerald-300">{formatNumber(data.average, precision)}</p>
          </div>
          <div className="text-center border-x border-slate-800/50">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Max</p>
            <p className="mt-2 text-lg font-semibold text-sky-300">{formatNumber(data.max, precision)}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Min</p>
            <p className="mt-2 text-lg font-semibold text-amber-300">{formatNumber(data.min, precision)}</p>
          </div>
        </div>
      </div>
    </DashboardTile>
  );
};

export default KpiCard;
