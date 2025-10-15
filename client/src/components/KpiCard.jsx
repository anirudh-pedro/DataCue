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
    <DashboardTile title={title} className="bg-gradient-to-br from-slate-900/95 to-slate-900/60">
      <div className="flex w-full flex-col justify-center gap-4 text-white">
        <div>
          <p className="text-4xl font-semibold tracking-tight">
            {formatNumber(data.primary_value, precision)}
          </p>
          <p className="text-xs uppercase tracking-wider text-slate-400">Total Value</p>
        </div>
        <div className="grid grid-cols-3 gap-4 text-xs text-slate-300">
          <div>
            <p className="font-semibold text-sm text-slate-200">Avg</p>
            <p>{formatNumber(data.average, precision)}</p>
          </div>
          <div>
            <p className="font-semibold text-sm text-slate-200">Max</p>
            <p>{formatNumber(data.max, precision)}</p>
          </div>
          <div>
            <p className="font-semibold text-sm text-slate-200">Min</p>
            <p>{formatNumber(data.min, precision)}</p>
          </div>
        </div>
      </div>
    </DashboardTile>
  );
};

export default KpiCard;
