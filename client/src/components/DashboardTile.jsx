import { FiDownload, FiMaximize2 } from 'react-icons/fi';

const DashboardTile = ({
  title,
  subtitle,
  children,
  onFullscreen,
  onDownload,
  className = '',
}) => {
  return (
    <div
      className={`group relative flex h-full flex-col rounded-2xl border border-slate-800/50 bg-gradient-to-br from-slate-900/90 to-slate-900/60 p-5 shadow-xl shadow-black/30 backdrop-blur-sm transition-all duration-300 hover:border-slate-700/70 hover:shadow-2xl hover:shadow-black/40 ${className}`.trim()}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="text-sm font-bold text-white leading-tight">{title}</h3>
          {subtitle ? (
            <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-1 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          {onFullscreen ? (
            <button
              onClick={onFullscreen}
              type="button"
              className="rounded-lg p-2 text-slate-400 transition-all hover:bg-slate-800/70 hover:text-white active:scale-95"
              aria-label="Enter fullscreen"
            >
              <FiMaximize2 className="text-sm" />
            </button>
          ) : null}
          {onDownload ? (
            <button
              onClick={onDownload}
              type="button"
              className="rounded-lg p-2 text-slate-400 transition-all hover:bg-slate-800/70 hover:text-white active:scale-95"
              aria-label="Download chart"
            >
              <FiDownload className="text-sm" />
            </button>
          ) : null}
        </div>
      </div>
      <div className="flex min-h-[280px] flex-1 overflow-hidden rounded-xl border border-slate-800/40 bg-slate-950/40 p-2">
        {children}
      </div>
    </div>
  );
};

export default DashboardTile;
