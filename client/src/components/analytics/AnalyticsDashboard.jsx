/**
 * AnalyticsDashboard - Power BI-style full-screen analytics dashboard
 * 
 * Features:
 * - 100vh full-screen layout with no vertical scrolling
 * - 12-column CSS grid with configurable row height
 * - Panel placement driven by backend JSON (x, y, w, h)
 * - Professional dark theme matching Power BI/Tableau aesthetics
 */

import { useMemo } from 'react';
import DashboardPanel from './DashboardPanel';
import PanelRenderer from './PanelRenderer';
import { FiRefreshCw, FiMaximize2, FiSettings, FiDownload } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

const DEFAULT_LAYOUT = {
  columns: 12,
  rowHeight: 100,
  gap: 16,
  headerHeight: 56,
};

const AnalyticsDashboard = ({
  dashboard,
  isLoading = false,
  onRefresh,
  onExport,
  onSettings,
}) => {
  // Merge default layout with dashboard layout
  const layout = useMemo(() => ({
    ...DEFAULT_LAYOUT,
    ...(dashboard?.layout || {}),
  }), [dashboard?.layout]);

  // Calculate grid dimensions
  const gridStyle = useMemo(() => {
    const headerHeight = layout.headerHeight;
    const gap = layout.gap;
    const padding = gap;
    
    // Available height = 100vh - header - padding
    const availableHeight = `calc(100vh - ${headerHeight}px - ${padding * 2}px)`;
    
    return {
      display: 'grid',
      gridTemplateColumns: `repeat(${layout.columns}, 1fr)`,
      gridAutoRows: `${layout.rowHeight}px`,
      gap: `${gap}px`,
      padding: `${padding}px`,
      height: availableHeight,
      overflow: 'hidden',
    };
  }, [layout]);

  // Parse panels from dashboard
  const panels = dashboard?.panels || dashboard?.dashboard?.charts?.map((chart, index) => ({
    id: chart.id || chart.chart_id || `panel_${index}`,
    type: chart.type || chart.chart_type,
    title: chart.title,
    subtitle: chart.description,
    // Backend returns Plotly figures with {data, layout}
    figure: chart.figure,
    // Also support raw data for custom rendering
    data: chart.data,
    config: {
      x_axis: chart.x_axis,
      y_axis: chart.y_axis,
      aggregation: chart.aggregation,
    },
    layout: chart.layout || getDefaultLayout(index, chart.type || chart.chart_type),
  })) || [];

  if (isLoading) {
    return (
      <div className="h-screen w-full bg-slate-950 flex flex-col">
        <DashboardHeader 
          title="Loading..." 
          isLoading={true}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-slate-400 animate-pulse">Generating dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!dashboard || panels.length === 0) {
    return (
      <div className="h-screen w-full bg-slate-950 flex flex-col">
        <DashboardHeader 
          title="Analytics Dashboard" 
          onRefresh={onRefresh}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800/50 flex items-center justify-center">
              <HiSparkles className="text-3xl text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">No Dashboard Data</h2>
            <p className="text-slate-400 text-sm">
              Upload a dataset to automatically generate insights and visualizations.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-slate-950 flex flex-col overflow-hidden">
      {/* Dashboard Header */}
      <DashboardHeader
        title={dashboard?.title || dashboard?.dashboard?.title || 'Analytics Dashboard'}
        subtitle={dashboard?.description || dashboard?.dashboard?.description}
        onRefresh={onRefresh}
        onExport={onExport}
        onSettings={onSettings}
      />

      {/* Grid Container */}
      <div style={gridStyle}>
        {panels.map((panel) => (
          <DashboardPanel
            key={panel.id}
            panel={panel}
            layout={layout}
          >
            <PanelRenderer panel={panel} />
          </DashboardPanel>
        ))}
      </div>
    </div>
  );
};

/**
 * Dashboard Header Bar
 */
const DashboardHeader = ({ 
  title, 
  subtitle, 
  isLoading,
  onRefresh, 
  onExport, 
  onSettings 
}) => (
  <header className="h-14 min-h-[56px] px-4 flex items-center justify-between border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-sm">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <HiSparkles className="text-white text-sm" />
      </div>
      <div>
        <h1 className="text-base font-semibold text-white leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-slate-400 leading-tight">{subtitle}</p>
        )}
      </div>
    </div>

    <div className="flex items-center gap-2">
      {onRefresh && (
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
          title="Refresh dashboard"
        >
          <FiRefreshCw className={`text-lg ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      )}
      {onExport && (
        <button
          onClick={onExport}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="Export dashboard"
        >
          <FiDownload className="text-lg" />
        </button>
      )}
      {onSettings && (
        <button
          onClick={onSettings}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="Dashboard settings"
        >
          <FiSettings className="text-lg" />
        </button>
      )}
    </div>
  </header>
);

/**
 * Get default layout for a panel based on its index and type
 * Used when backend doesn't provide explicit layout
 */
function getDefaultLayout(index, chartType) {
  // KPIs: small, top row
  if (chartType === 'kpi') {
    return {
      x: (index % 4) * 3,
      y: 0,
      w: 3,
      h: 1,
    };
  }

  // Pie charts: medium square
  if (chartType === 'pie') {
    return {
      x: (index % 2) * 6,
      y: Math.floor(index / 2) + 1,
      w: 6,
      h: 3,
    };
  }

  // Tables: wide, short
  if (chartType === 'table') {
    return {
      x: 0,
      y: index + 1,
      w: 12,
      h: 2,
    };
  }

  // Default: half width, standard height
  return {
    x: (index % 2) * 6,
    y: Math.floor(index / 2) + 1,
    w: 6,
    h: 3,
  };
}

export default AnalyticsDashboard;
