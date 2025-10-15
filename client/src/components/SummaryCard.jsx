const SummaryCard = ({ label, value, badge, badgeKey, icon: Icon }) => {
  const ratingStyles = {
    excellent: 'border border-emerald-400/40 bg-emerald-500/20 text-emerald-200',
    good: 'border border-sky-400/40 bg-sky-500/20 text-sky-200',
    fair: 'border border-amber-400/40 bg-amber-500/20 text-amber-200',
    poor: 'border border-rose-400/40 bg-rose-500/20 text-rose-200',
  };

  return (
    <div className="rounded-2xl border border-slate-800/60 bg-slate-900/60 p-4 shadow-lg shadow-black/10">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400/90 flex items-center gap-2">
        {Icon ? <Icon className="text-base text-slate-300" /> : null}
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
      {badge ? (
        <span
          className={`mt-4 inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-semibold ${
            badgeKey ? ratingStyles[badgeKey] || 'border border-slate-700 bg-slate-800 text-slate-200' : ''
          }`}
        >
          {badge}
        </span>
      ) : null}
    </div>
  );
};

export default SummaryCard;
