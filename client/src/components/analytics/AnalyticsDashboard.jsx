/**
 * AnalyticsDashboard - Professional dark dashboard like Power BI/Tableau
 * 
 * Features:
 * - Dark theme with cyan/teal accent colors
 * - KPI cards with icons at top row
 * - Smart auto-placement for optimal layout
 * - Responsive grid system
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardPanel from './DashboardPanel';
import PanelRenderer from './PanelRenderer';
import KpiCard from './KpiCard';
import { FiRefreshCw, FiDownload, FiArrowLeft, FiShare2, FiMaximize2 } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

/**
 * Smart layout calculator - Power BI style grid
 */
function calculateSmartLayout(panels) {
  // Separate panel types
  const kpis = panels.filter(p => p.type?.toLowerCase() === 'kpi');
  const charts = panels.filter(p => p.type?.toLowerCase() !== 'kpi' && p.type?.toLowerCase() !== 'insights');
  const insights = panels.filter(p => p.type?.toLowerCase() === 'insights');
  
  const layoutPanels = [];
  
  // Chart sizing based on type
  const chartSizes = {
    pie: { w: 4, h: 2 },
    donut: { w: 4, h: 2 },
    histogram: { w: 4, h: 2 },
    bar: { w: 4, h: 2 },
    grouped_bar: { w: 4, h: 2 },
    line: { w: 4, h: 2 },
    area: { w: 4, h: 2 },
    time_series: { w: 6, h: 2 },
    scatter: { w: 4, h: 2 },
    heatmap: { w: 6, h: 2 },
    table: { w: 6, h: 2 },
    default: { w: 4, h: 2 }
  };
  
  let currentCol = 0;
  let currentRow = 0;
  
  charts.forEach((chart, index) => {
    const type = chart.type?.toLowerCase() || 'default';
    let { w, h } = chartSizes[type] || chartSizes.default;
    
    // First chart larger for visual impact
    if (index === 0 && charts.length > 2) {
      w = 6;
    }
    
    // Check if fits in current row
    if (currentCol + w > 12) {
      currentCol = 0;
      currentRow += 2;
    }
    
    layoutPanels.push({
      ...chart,
      gridLayout: { x: currentCol, y: currentRow, w, h },
    });
    
    currentCol += w;
  });
  
  // Add insights at bottom as full width
  if (insights.length > 0) {
    if (currentCol !== 0) currentRow += 2;
    layoutPanels.push({
      ...insights[0],
      gridLayout: { x: 0, y: currentRow, w: 12, h: 1 },
    });
  }
  
  return { kpis, chartPanels: layoutPanels, insights };
}

const AnalyticsDashboard = ({
  dashboard,
  isLoading = false,
  onRefresh,
  onExport,
}) => {
  const navigate = useNavigate();

  // Parse and layout panels
  const { kpis, chartPanels, insights: panelInsights } = useMemo(() => {
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

  // Get insights from dashboard
  const insights = dashboard?.rawInsights || [];
  
  // Dashboard title
  const dashboardTitle = dashboard?.title || dashboard?.dashboard?.title || 'Sales Dashboard';

  if (isLoading) {
    return <LoadingState />;
  }

  if (!dashboard || chartPanels.length === 0) {
    return <EmptyState onBack={() => navigate('/chat')} onRefresh={onRefresh} />;
  }

  return (
    <div className="min-h-screen bg-[#0d1117]">
      {/* Header Bar */}
      <header className="bg-[#161b22] border-b border-gray-800/50 sticky top-0 z-50">
        <div className="px-4 py-3 flex items-center justify-between">
          {/* Left: Back + Title */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/chat')}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
            >
              <FiArrowLeft className="text-lg" />
            </button>
            <h1 className="text-lg font-semibold text-white">{dashboardTitle}</h1>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            <button onClick={onRefresh} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white" title="Refresh">
              <FiRefreshCw className="text-lg" />
            </button>
            <button onClick={onExport} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white" title="Export">
              <FiDownload className="text-lg" />
            </button>
            <button className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white" title="Share">
              <FiShare2 className="text-lg" />
            </button>
            <button className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white" title="Fullscreen">
              <FiMaximize2 className="text-lg" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4">
        {/* KPI Cards Row */}
        {kpis.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {kpis.slice(0, 4).map((kpi, index) => (
              <KpiCard key={kpi.id || index} kpi={kpi} index={index} />
            ))}
          </div>
        )}

        {/* Charts Grid */}
        <div 
          className="grid gap-3"
          style={{
            gridTemplateColumns: 'repeat(12, 1fr)',
            gridAutoRows: 'minmax(220px, auto)',
          }}
        >
          {chartPanels.map((panel) => (
            <div
              key={panel.id}
              style={{
                gridColumn: `span ${panel.gridLayout?.w || 4}`,
                gridRow: `span ${panel.gridLayout?.h || 2}`,
              }}
            >
              <DashboardPanel panel={panel}>
                <PanelRenderer panel={panel} />
              </DashboardPanel>
            </div>
          ))}
        </div>
        
        {/* Insights Section */}
        {insights.length > 0 && (
          <div className="mt-4 bg-[#161b22] rounded-lg border border-gray-800/50 p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <HiSparkles className="text-amber-400" />
              Key Insights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {insights.map((insight, index) => (
                <div 
                  key={index}
                  className="p-3 bg-[#21262d] border border-gray-700/50 rounded-lg text-sm text-gray-300"
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
 * Loading State - Dark Theme
 */
const LoadingState = () => (
  <div className="min-h-screen bg-[#1b1b1b] flex items-center justify-center">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-gray-700 border-t-amber-500 rounded-full animate-spin mx-auto mb-4" />
      <p className="text-gray-400">Generating dashboard...</p>
    </div>
  </div>
);

/**
 * Empty State - Dark Theme
 */
const EmptyState = ({ onBack, onRefresh }) => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#1b1b1b] flex items-center justify-center">
      <div className="text-center max-w-md p-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#333333] flex items-center justify-center">
          <HiSparkles className="text-3xl text-gray-500" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">No Dashboard Data</h2>
        <p className="text-gray-400 text-sm mb-6">
          Upload a dataset to automatically generate insights and visualizations.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate('/chat')}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
          >
            Go to Chat
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-[#333333] border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium"
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
