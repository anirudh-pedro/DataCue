/**
 * DashboardPanel - Individual panel wrapper for analytics dashboard
 * 
 * Positions itself using CSS Grid based on layout config:
 * - x: grid column start (0-indexed)
 * - y: grid row start (0-indexed)
 * - w: column span
 * - h: row span
 */

import { useMemo } from 'react';
import { FiMaximize2, FiMoreHorizontal, FiRefreshCw } from 'react-icons/fi';

const DashboardPanel = ({
  panel,
  layout,
  children,
  onMaximize,
  onRefresh,
  onOptions,
}) => {
  // Calculate grid positioning
  const panelStyle = useMemo(() => {
    const { x = 0, y = 0, w = 6, h = 3 } = panel.layout || {};
    
    return {
      gridColumn: `${x + 1} / span ${w}`,
      gridRow: `${y + 1} / span ${h}`,
    };
  }, [panel.layout]);

  // Determine if panel is compact (1 row height)
  const isCompact = (panel.layout?.h || 3) === 1;

  return (
    <div
      style={panelStyle}
      className={`
        group relative flex flex-col
        rounded-xl border border-slate-800/60
        bg-gradient-to-br from-slate-900/95 to-slate-900/80
        shadow-lg shadow-black/20
        backdrop-blur-sm
        transition-all duration-200
        hover:border-slate-700/80
        hover:shadow-xl hover:shadow-black/30
        overflow-hidden
      `}
    >
      {/* Panel Header */}
      <div className={`
        flex items-center justify-between
        border-b border-slate-800/40
        ${isCompact ? 'px-3 py-2' : 'px-4 py-3'}
      `}>
        <div className="flex-1 min-w-0">
          <h3 className={`
            font-medium text-white truncate
            ${isCompact ? 'text-xs' : 'text-sm'}
          `}>
            {panel.title}
          </h3>
          {panel.subtitle && !isCompact && (
            <p className="text-xs text-slate-500 truncate mt-0.5">
              {panel.subtitle}
            </p>
          )}
        </div>

        {/* Panel Actions - Visible on hover */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {onRefresh && (
            <button
              onClick={() => onRefresh(panel.id)}
              className="p-1.5 rounded-md text-slate-500 hover:text-white hover:bg-slate-800/70 transition-colors"
              title="Refresh"
            >
              <FiRefreshCw className="text-xs" />
            </button>
          )}
          {onMaximize && (
            <button
              onClick={() => onMaximize(panel.id)}
              className="p-1.5 rounded-md text-slate-500 hover:text-white hover:bg-slate-800/70 transition-colors"
              title="Maximize"
            >
              <FiMaximize2 className="text-xs" />
            </button>
          )}
          {onOptions && (
            <button
              onClick={() => onOptions(panel.id)}
              className="p-1.5 rounded-md text-slate-500 hover:text-white hover:bg-slate-800/70 transition-colors"
              title="Options"
            >
              <FiMoreHorizontal className="text-xs" />
            </button>
          )}
        </div>
      </div>

      {/* Panel Content */}
      <div className="flex-1 p-2 overflow-hidden">
        {children}
      </div>
    </div>
  );
};

export default DashboardPanel;
