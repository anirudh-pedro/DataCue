/**
 * DashboardPanel - Power BI-style professional dark panel wrapper
 */

import { FiMoreVertical, FiMaximize2 } from 'react-icons/fi';

// Accent colors for different chart types (Power BI palette)
const chartAccentColors = {
  bar: '#118DFF',       // Power BI Blue
  grouped_bar: '#118DFF',
  line: '#12B5CB',      // Teal
  time_series: '#12B5CB',
  area: '#12B5CB',
  pie: '#B845A7',       // Purple
  donut: '#B845A7',
  scatter: '#1AAB40',   // Green
  scatter_plot: '#1AAB40',
  histogram: '#E66C37', // Orange
  heatmap: '#D64550',   // Red
  correlation_heatmap: '#D64550',
  kpi: '#118DFF',       // Blue
  table: '#744EC2',     // Violet
  insights: '#D9B300',  // Yellow/Gold
  default: '#118DFF',
};

const DashboardPanel = ({
  panel,
  size = 'medium',
  children,
}) => {
  const chartType = panel.type?.toLowerCase() || 'default';
  const accentColor = chartAccentColors[chartType] || chartAccentColors.default;
  const isKpi = chartType === 'kpi';

  return (
    <div
      className={`
        group relative flex flex-col h-full
        bg-[#161b22] rounded-lg
        border border-gray-800/50
        hover:border-gray-700/50
        transition-all duration-200
        overflow-hidden
      `}
    >
      {/* Panel Header - Only show for non-KPI panels */}
      {!isKpi && panel.title && (
        <div className="flex items-start justify-between px-4 pt-3 pb-2 flex-shrink-0">
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-white truncate">
              {panel.title}
            </h3>
            {panel.subtitle && (
              <p className="text-xs text-gray-500 mt-0.5 truncate">
                {panel.subtitle}
              </p>
            )}
          </div>
          
          {/* Action buttons - visible on hover */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
            <button 
              className="p-1 hover:bg-gray-700/30 rounded text-gray-500 hover:text-gray-300"
              title="Expand"
            >
              <FiMaximize2 className="text-xs" />
            </button>
            <button 
              className="p-1 hover:bg-gray-700/30 rounded text-gray-500 hover:text-gray-300"
              title="More options"
            >
              <FiMoreVertical className="text-xs" />
            </button>
          </div>
        </div>
      )}
      
      {/* Panel Content */}
      <div className={`flex-1 ${isKpi ? 'p-2' : 'px-3 pb-3'} min-h-0`}>
        {children}
      </div>
    </div>
  );
};

export default DashboardPanel;
