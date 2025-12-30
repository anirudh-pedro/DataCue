/**
 * DashboardPanel - Power BI-style professional panel wrapper
 * 
 * Features:
 * - Clean white card design
 * - Compact header with title and subtitle
 * - Colored accent bar based on chart type
 * - Hover effects for interactivity
 * - Responsive sizing
 */

import { FiMoreVertical, FiMaximize2 } from 'react-icons/fi';

// Accent colors for different chart types
const chartAccentColors = {
  bar: '#6366f1',       // Indigo
  grouped_bar: '#6366f1',
  line: '#06b6d4',      // Cyan
  time_series: '#06b6d4',
  pie: '#8b5cf6',       // Purple
  donut: '#8b5cf6',
  scatter: '#10b981',   // Emerald
  scatter_plot: '#10b981',
  histogram: '#f59e0b', // Amber
  heatmap: '#ef4444',   // Red
  correlation_heatmap: '#ef4444',
  kpi: '#3b82f6',       // Blue
  table: '#64748b',     // Slate
  insights: '#f59e0b',  // Amber
  default: '#6366f1',
};

const DashboardPanel = ({
  panel,
  size = 'medium',
  children,
}) => {
  const chartType = panel.type?.toLowerCase() || 'default';
  const accentColor = chartAccentColors[chartType] || chartAccentColors.default;
  const isKpi = chartType === 'kpi';
  
  // Size-based height
  const heightClasses = {
    kpi: 'h-full min-h-[100px]',
    small: 'h-full min-h-[280px]',
    medium: 'h-full min-h-[280px]',
    large: 'h-full min-h-[280px]',
    full: 'h-full min-h-[280px]',
  };

  return (
    <div
      className={`
        group relative flex flex-col
        bg-white rounded-lg
        border border-gray-200
        shadow-sm hover:shadow-md
        transition-shadow duration-200
        overflow-hidden
        ${heightClasses[size] || heightClasses.medium}
      `}
    >
      {/* Top accent bar */}
      <div 
        className="h-1 w-full flex-shrink-0"
        style={{ backgroundColor: accentColor }}
      />
      
      {/* Panel Header - Only show for non-KPI panels */}
      {!isKpi && panel.title && (
        <div className="flex items-start justify-between px-3 pt-3 pb-1 flex-shrink-0">
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-gray-900 truncate">
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
              className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
              title="Expand"
            >
              <FiMaximize2 className="text-xs" />
            </button>
            <button 
              className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
              title="More options"
            >
              <FiMoreVertical className="text-xs" />
            </button>
          </div>
        </div>
      )}
      
      {/* Panel Content */}
      <div className={`flex-1 ${isKpi ? 'p-3' : 'px-3 pb-3'} min-h-0`}>
        {children}
      </div>
    </div>
  );
};

export default DashboardPanel;
