/**
 * AnalyticsDashboard - Power BI-style professional analytics dashboard
 * 
 * Features:
 * - Light professional theme matching Power BI/Tableau
 * - Smart auto-placement algorithm for optimal layout
 * - Compact KPI cards at top
 * - Responsive grid with different panel sizes
 * - Header with share and export options
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardPanel from './DashboardPanel';
import PanelRenderer from './PanelRenderer';
import { FiRefreshCw, FiDownload, FiArrowLeft, FiShare2, FiMaximize2, FiSearch } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

/**
 * Smart layout calculator - determines optimal grid placement
 */
function calculateSmartLayout(panels) {
  const layoutPanels = [];
  let currentRow = 0;
  
  // Separate panel types
  const kpis = panels.filter(p => p.type?.toLowerCase() === 'kpi');
  const charts = panels.filter(p => p.type?.toLowerCase() !== 'kpi' && p.type?.toLowerCase() !== 'insights');
  const insights = panels.filter(p => p.type?.toLowerCase() === 'insights');
  
  // Row 0: KPIs (compact, 3 columns each for up to 4 KPIs)
  if (kpis.length > 0) {
    const kpiWidth = Math.floor(12 / Math.min(kpis.length, 4));
    kpis.slice(0, 4).forEach((kpi, i) => {
      layoutPanels.push({
        ...kpi,
        gridLayout: { x: i * kpiWidth, y: 0, w: kpiWidth, h: 1 },
        size: 'kpi'
      });
    });
    currentRow = 1;
  }
  
  // Smart chart placement - vary sizes for visual interest
  const chartSizes = {
    pie: { w: 4, h: 2, size: 'small' },
    donut: { w: 4, h: 2, size: 'small' },
    histogram: { w: 4, h: 2, size: 'medium' },
    bar: { w: 6, h: 2, size: 'medium' },
    grouped_bar: { w: 6, h: 2, size: 'medium' },
    line: { w: 6, h: 2, size: 'medium' },
    time_series: { w: 8, h: 2, size: 'large' },
    scatter: { w: 6, h: 2, size: 'medium' },
    scatter_plot: { w: 6, h: 2, size: 'medium' },
    heatmap: { w: 6, h: 2, size: 'medium' },
    table: { w: 12, h: 2, size: 'full' },
    default: { w: 6, h: 2, size: 'medium' }
  };
  
  let currentCol = 0;
  let rowHeight = 2;
  
  charts.forEach((chart, index) => {
    const type = chart.type?.toLowerCase() || 'default';
    const sizing = chartSizes[type] || chartSizes.default;
    
    // Vary first chart to be larger for impact
    let { w, h, size } = sizing;
    if (index === 0 && charts.length > 2) {
      w = 8;
      h = 2;
      size = 'large';
    }
    
    // Check if fits in current row
    if (currentCol + w > 12) {
      currentCol = 0;
      currentRow += rowHeight;
    }
    
    layoutPanels.push({
      ...chart,
      gridLayout: { x: currentCol, y: currentRow, w, h },
      size
    });
    
    currentCol += w;
    if (currentCol >= 12) {
      currentCol = 0;
      currentRow += rowHeight;
    }
  });
  
  // Add insights at bottom
  if (insights.length > 0) {
    if (currentCol !== 0) {
      currentRow += rowHeight;
    }
    layoutPanels.push({
      ...insights[0],
      gridLayout: { x: 0, y: currentRow, w: 12, h: 1 },
      size: 'full'
    });
  }
  
  return layoutPanels;
}

const AnalyticsDashboard = ({
  dashboard,
  isLoading = false,
  onRefresh,
  onExport,
}) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  // Parse and layout panels
  const layoutPanels = useMemo(() => {
    const rawPanels = dashboard?.panels || dashboard?.dashboard?.charts?.map((chart, index) => ({
      id: chart.id || chart.chart_id || `panel_${index}`,
      type: chart.type || chart.chart_type,
      title: chart.title,
      subtitle: chart.description,
      figure: chart.figure,
      data: chart.data,
      config: {
        x_axis: chart.x_axis,
        y_axis: chart.y_axis,
        aggregation: chart.aggregation,
      },
    })) || [];
    
    return calculateSmartLayout(rawPanels);
  }, [dashboard]);

  // Get insights for separate display
  const insights = dashboard?.rawInsights || [];

  if (isLoading) {
    return <LoadingState />;
  }

  if (!dashboard || layoutPanels.length === 0) {
    return <EmptyState onBack={() => navigate('/chat')} onRefresh={onRefresh} />;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header Bar */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="px-4 py-2 flex items-center justify-between gap-4">
          {/* Left: Navigation and Title */}
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => navigate('/chat')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
            >
              <FiArrowLeft className="text-lg" />
            </button>
            
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <HiSparkles className="text-white text-sm" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-gray-900 truncate max-w-xs">
                  {dashboard?.title || dashboard?.dashboard?.title || 'Executive Dashboard'}
                </h1>
                <p className="text-xs text-gray-500">
                  {layoutPanels.length} visualizations
                </p>
              </div>
            </div>
          </div>

          {/* Center: Search */}
          <div className="hidden md:flex flex-1 max-w-md mx-4">
            <div className="relative w-full">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm" />
              <input
                type="text"
                placeholder="Ask a question about this dashboard..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-1">
            <button
              onClick={onRefresh}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
              title="Refresh"
            >
              <FiRefreshCw className="text-lg" />
            </button>
            <button
              onClick={onExport}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
              title="Export"
            >
              <FiDownload className="text-lg" />
            </button>
            <button
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
              title="Share"
            >
              <FiShare2 className="text-lg" />
            </button>
            <button
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
              title="Fullscreen"
            >
              <FiMaximize2 className="text-lg" />
            </button>
          </div>
        </div>
      </header>

      {/* Dashboard Grid */}
      <div className="p-3 md:p-4">
        <div 
          className="grid gap-3"
          style={{
            gridTemplateColumns: 'repeat(12, 1fr)',
            gridAutoRows: 'minmax(140px, auto)',
          }}
        >
          {layoutPanels.map((panel) => (
            <div
              key={panel.id}
              style={{
                gridColumn: `span ${panel.gridLayout?.w || 6}`,
                gridRow: `span ${panel.gridLayout?.h || 2}`,
              }}
            >
              <DashboardPanel panel={panel} size={panel.size}>
                <PanelRenderer panel={panel} />
              </DashboardPanel>
            </div>
          ))}
        </div>
        
        {/* Insights Section */}
        {insights.length > 0 && (
          <div className="mt-4 bg-white rounded-lg border border-gray-200 shadow-sm p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-1 h-4 bg-amber-500 rounded-full"></span>
              Key Insights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {insights.map((insight, index) => (
                <div 
                  key={index}
                  className="p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm text-gray-700"
                >
                  {insight}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Loading State
 */
const LoadingState = () => (
  <div className="min-h-screen bg-gray-100 flex items-center justify-center">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
      <p className="text-gray-600">Generating dashboard...</p>
    </div>
  </div>
);

/**
 * Empty State
 */
const EmptyState = ({ onBack, onRefresh }) => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center max-w-md p-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-200 flex items-center justify-center">
          <HiSparkles className="text-3xl text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Dashboard Data</h2>
        <p className="text-gray-500 text-sm mb-6">
          Upload a dataset to automatically generate insights and visualizations.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate('/chat')}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
          >
            Go to Chat
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
