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
      className={`group relative flex h-full flex-col rounded-2xl border border-gray-800/60 bg-gray-900/80 p-4 shadow-lg shadow-black/20 transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-black/30 ${className}`.trim()}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          {subtitle ? (
            <p className="text-xs text-slate-400/80">{subtitle}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          {onFullscreen ? (
            <button
              onClick={onFullscreen}
              type="button"
              className="rounded-lg p-1.5 transition-colors hover:bg-gray-800/80 hover:text-white"
              aria-label="Enter fullscreen"
            >
              <FiMaximize2 className="text-sm" />
            </button>
          ) : null}
          {onDownload ? (
            <button
              onClick={onDownload}
              type="button"
              className="rounded-lg p-1.5 transition-colors hover:bg-gray-800/80 hover:text-white"
              aria-label="Download chart"
            >
              <FiDownload className="text-sm" />
            </button>
          ) : null}
        </div>
      </div>
      <div className="flex min-h-[260px] flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  );
};

export default DashboardTile;
