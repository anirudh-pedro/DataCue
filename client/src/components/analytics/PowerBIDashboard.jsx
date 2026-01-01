/**
 * PowerBIDashboard - Full-screen Power BI-style analytics dashboard
 * 
 * Features:
 * - Dark theme matching Power BI Desktop
 * - KPI cards with trend indicators
 * - Smart grid layout for charts
 * - Filter sidebar
 * - Export and share capabilities
 */

import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { 
  FiArrowLeft, 
  FiRefreshCw, 
  FiDownload, 
  FiShare2, 
  FiMaximize2,
  FiFilter,
  FiCalendar,
  FiChevronDown,
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiDollarSign,
  FiUsers,
  FiShoppingCart,
  FiPackage,
  FiActivity,
  FiBarChart2,
  FiPieChart,
  FiGrid,
  FiX
} from 'react-icons/fi';
import { HiSparkles, HiLightBulb } from 'react-icons/hi2';

// ============================================================================
// POWER BI COLOR PALETTE
// ============================================================================
const POWER_BI_COLORS = {
  // Primary accent colors
  blue: '#118DFF',
  teal: '#12B5CB', 
  orange: '#E66C37',
  purple: '#B845A7',
  yellow: '#D9B300',
  green: '#1AAB40',
  red: '#D64550',
  navy: '#12239E',
  
  // Background colors (dark theme)
  bgPrimary: '#0d1117',
  bgSecondary: '#161b22',
  bgTertiary: '#21262d',
  bgHover: '#30363d',
  
  // Border colors
  border: 'rgba(48, 54, 61, 0.8)',
  borderHover: 'rgba(110, 118, 129, 0.5)',
  
  // Text colors
  textPrimary: '#f0f6fc',
  textSecondary: '#8b949e',
  textMuted: '#6e7681',
};

const CHART_COLORS = [
  POWER_BI_COLORS.blue,
  POWER_BI_COLORS.teal,
  POWER_BI_COLORS.orange,
  POWER_BI_COLORS.purple,
  POWER_BI_COLORS.yellow,
  POWER_BI_COLORS.green,
  POWER_BI_COLORS.red,
  POWER_BI_COLORS.navy,
];

// ============================================================================
// PLOTLY THEME
// ============================================================================
const PLOTLY_THEME = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: {
    family: 'Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif',
    color: POWER_BI_COLORS.textSecondary,
    size: 11,
  },
  margin: { t: 20, r: 20, b: 50, l: 60 },
  xaxis: {
    gridcolor: 'rgba(139, 148, 158, 0.15)',
    zerolinecolor: 'rgba(139, 148, 158, 0.3)',
    tickfont: { size: 10, color: POWER_BI_COLORS.textMuted },
    linecolor: 'rgba(139, 148, 158, 0.3)',
    showgrid: true,
  },
  yaxis: {
    gridcolor: 'rgba(139, 148, 158, 0.15)',
    zerolinecolor: 'rgba(139, 148, 158, 0.3)',
    tickfont: { size: 10, color: POWER_BI_COLORS.textMuted },
    linecolor: 'rgba(139, 148, 158, 0.3)',
    showgrid: true,
  },
  colorway: CHART_COLORS,
  hoverlabel: {
    bgcolor: POWER_BI_COLORS.bgTertiary,
    bordercolor: POWER_BI_COLORS.border,
    font: { color: POWER_BI_COLORS.textPrimary, size: 12 },
  },
  legend: {
    font: { color: POWER_BI_COLORS.textSecondary, size: 10 },
    bgcolor: 'transparent',
    orientation: 'h',
    y: -0.2,
    x: 0.5,
    xanchor: 'center',
  },
};

// ============================================================================
// KPI CARD COMPONENT
// ============================================================================
const KpiCard = ({ title, value, trend, trendValue, icon: IconComponent, colorIndex = 0 }) => {
  const colors = [
    { accent: POWER_BI_COLORS.blue, bg: 'rgba(17, 141, 255, 0.12)' },
    { accent: POWER_BI_COLORS.teal, bg: 'rgba(18, 181, 203, 0.12)' },
    { accent: POWER_BI_COLORS.orange, bg: 'rgba(230, 108, 55, 0.12)' },
    { accent: POWER_BI_COLORS.purple, bg: 'rgba(184, 69, 167, 0.12)' },
  ];
  
  const color = colors[colorIndex % colors.length];
  const Icon = IconComponent || FiBarChart2;
  
  // Determine trend icon and color
  const getTrendDisplay = () => {
    if (trend === 'up') return { Icon: FiTrendingUp, color: '#1AAB40', text: `+${trendValue}%` };
    if (trend === 'down') return { Icon: FiTrendingDown, color: '#D64550', text: `-${Math.abs(trendValue)}%` };
    return { Icon: FiMinus, color: POWER_BI_COLORS.textMuted, text: '0%' };
  };
  
  const trendDisplay = trendValue !== undefined ? getTrendDisplay() : null;

  // Format value
  const formatValue = (val) => {
    if (val === null || val === undefined) return '—';
    const num = typeof val === 'string' ? parseFloat(val.replace(/[,$]/g, '')) : val;
    if (isNaN(num)) return val;
    if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
    return Number.isInteger(num) ? num.toLocaleString() : num.toFixed(2);
  };

  return (
    <div 
      className="rounded-lg p-4 transition-all duration-200 hover:scale-[1.02] cursor-pointer"
      style={{ 
        backgroundColor: POWER_BI_COLORS.bgSecondary,
        border: `1px solid ${POWER_BI_COLORS.border}`,
      }}
    >
      {/* Header: Icon + Title */}
      <div className="flex items-center gap-3 mb-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: color.bg }}
        >
          <Icon className="text-xl" style={{ color: color.accent }} />
        </div>
        <span 
          className="text-xs font-medium uppercase tracking-wider truncate"
          style={{ color: POWER_BI_COLORS.textMuted }}
        >
          {title}
        </span>
      </div>
      
      {/* Value */}
      <div className="flex items-end justify-between">
        <span 
          className="text-3xl font-bold tracking-tight"
          style={{ color: color.accent }}
        >
          {formatValue(value)}
        </span>
        
        {/* Trend */}
        {trendDisplay && (
          <div 
            className="flex items-center gap-1 text-sm font-medium"
            style={{ color: trendDisplay.color }}
          >
            <trendDisplay.Icon className="text-sm" />
            <span>{trendDisplay.text}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// CHART PANEL COMPONENT
// ============================================================================
const ChartPanel = ({ title, subtitle, children, onExpand }) => {
  return (
    <div 
      className="rounded-lg h-full flex flex-col overflow-hidden"
      style={{ 
        backgroundColor: POWER_BI_COLORS.bgSecondary,
        border: `1px solid ${POWER_BI_COLORS.border}`,
      }}
    >
      {/* Header */}
      <div className="px-4 pt-3 pb-2 flex items-center justify-between flex-shrink-0">
        <div className="min-w-0 flex-1">
          <h3 
            className="text-sm font-semibold truncate"
            style={{ color: POWER_BI_COLORS.textPrimary }}
          >
            {title}
          </h3>
          {subtitle && (
            <p 
              className="text-xs truncate mt-0.5"
              style={{ color: POWER_BI_COLORS.textMuted }}
            >
              {subtitle}
            </p>
          )}
        </div>
        {onExpand && (
          <button 
            onClick={onExpand}
            className="p-1.5 rounded hover:bg-gray-700/30 transition-colors"
            style={{ color: POWER_BI_COLORS.textMuted }}
          >
            <FiMaximize2 className="text-sm" />
          </button>
        )}
      </div>
      
      {/* Chart Content */}
      <div className="flex-1 px-3 pb-3 min-h-0">
        {children}
      </div>
    </div>
  );
};

// ============================================================================
// CHART RENDERER
// ============================================================================
const ChartRenderer = ({ panel }) => {
  const { type, figure, data, config } = panel;
  const chartType = type?.toLowerCase() || 'bar';
  
  // If backend provides a plotly figure, use it directly
  if (figure?.data) {
    return (
      <Plot
        data={figure.data}
        layout={{
          ...PLOTLY_THEME,
          ...figure.layout,
          autosize: true,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    );
  }
  
  // Build chart from raw data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div 
        className="h-full flex items-center justify-center"
        style={{ color: POWER_BI_COLORS.textMuted }}
      >
        No data available
      </div>
    );
  }
  
  const columns = Object.keys(data[0] || {});
  const xKey = config?.x_axis || columns[0];
  const yKey = config?.y_axis || columns[1] || columns[0];
  
  const xValues = data.map(d => d[xKey]);
  const yValues = data.map(d => d[yKey]);
  
  let traces = [];
  let layout = { ...PLOTLY_THEME };
  
  switch (chartType) {
    case 'bar':
    case 'grouped_bar':
      traces = [{
        type: 'bar',
        x: xValues,
        y: yValues,
        marker: { color: POWER_BI_COLORS.blue, line: { width: 0 } },
        hovertemplate: `<b>%{x}</b><br>${yKey}: %{y:,.0f}<extra></extra>`,
      }];
      layout.bargap = 0.3;
      break;
      
    case 'line':
    case 'time_series':
    case 'area':
      traces = [{
        type: 'scatter',
        mode: 'lines',
        x: xValues,
        y: yValues,
        line: { color: POWER_BI_COLORS.teal, width: 2.5, shape: 'spline' },
        fill: chartType === 'area' ? 'tozeroy' : 'none',
        fillcolor: 'rgba(18, 181, 203, 0.15)',
        hovertemplate: `<b>%{x}</b><br>${yKey}: %{y:,.2f}<extra></extra>`,
      }];
      break;
      
    case 'pie':
    case 'donut':
      traces = [{
        type: 'pie',
        labels: xValues,
        values: yValues,
        hole: chartType === 'donut' ? 0.5 : 0.45,
        marker: { colors: CHART_COLORS, line: { color: POWER_BI_COLORS.bgPrimary, width: 2 } },
        textposition: 'inside',
        textinfo: 'percent',
        textfont: { size: 11, color: '#fff' },
        hovertemplate: '<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>',
      }];
      layout.showlegend = true;
      layout.margin = { t: 10, r: 10, b: 40, l: 10 };
      break;
      
    case 'scatter':
    case 'scatter_plot':
      traces = [{
        type: 'scatter',
        mode: 'markers',
        x: xValues,
        y: yValues,
        marker: { 
          color: POWER_BI_COLORS.purple, 
          size: 8,
          opacity: 0.7,
        },
        hovertemplate: `${xKey}: %{x}<br>${yKey}: %{y}<extra></extra>`,
      }];
      break;
      
    case 'histogram':
      traces = [{
        type: 'histogram',
        x: data.map(d => d[xKey]),
        marker: { color: POWER_BI_COLORS.orange, line: { color: POWER_BI_COLORS.bgPrimary, width: 1 } },
        hovertemplate: 'Range: %{x}<br>Count: %{y}<extra></extra>',
      }];
      break;
      
    default:
      traces = [{
        type: 'bar',
        x: xValues,
        y: yValues,
        marker: { color: POWER_BI_COLORS.blue },
      }];
  }
  
  return (
    <Plot
      data={traces}
      layout={{ ...layout, autosize: true }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler
    />
  );
};

// ============================================================================
// INSIGHTS PANEL
// ============================================================================
const InsightsPanel = ({ insights }) => {
  if (!insights || insights.length === 0) return null;
  
  return (
    <div 
      className="rounded-lg p-4"
      style={{ 
        backgroundColor: POWER_BI_COLORS.bgSecondary,
        border: `1px solid ${POWER_BI_COLORS.border}`,
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <HiLightBulb className="text-lg" style={{ color: POWER_BI_COLORS.yellow }} />
        <h3 
          className="text-sm font-semibold"
          style={{ color: POWER_BI_COLORS.textPrimary }}
        >
          AI Insights
        </h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {insights.map((insight, index) => (
          <div 
            key={index}
            className="p-3 rounded-lg text-sm"
            style={{ 
              backgroundColor: POWER_BI_COLORS.bgTertiary,
              color: POWER_BI_COLORS.textSecondary,
              border: `1px solid ${POWER_BI_COLORS.border}`,
            }}
          >
            {insight}
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================
const PowerBIDashboard = ({
  dashboard,
  isLoading = false,
  onRefresh,
  onExport,
}) => {
  const navigate = useNavigate();
  const [showFilters, setShowFilters] = useState(false);
  
  // Parse dashboard data
  const { kpis, charts, insights, title } = useMemo(() => {
    if (!dashboard) return { kpis: [], charts: [], insights: [], title: 'Analytics Dashboard' };
    
    const panels = dashboard.panels || [];
    const rawCharts = dashboard.dashboard?.charts || [];
    
    // Separate KPIs from charts
    const kpiPanels = panels.filter(p => p.type?.toLowerCase() === 'kpi');
    const chartPanels = panels.filter(p => 
      p.type?.toLowerCase() !== 'kpi' && 
      p.type?.toLowerCase() !== 'insights'
    );
    
    // If no panels, try to extract from dashboard.charts
    if (chartPanels.length === 0 && rawCharts.length > 0) {
      rawCharts.forEach((chart, i) => {
        if ((chart.type || chart.chart_type)?.toLowerCase() === 'kpi') {
          kpiPanels.push({
            id: chart.id || `kpi_${i}`,
            type: 'kpi',
            title: chart.title,
            value: chart.value || chart.data?.[0]?.[Object.keys(chart.data?.[0] || {})[0]],
            data: chart.data,
            figure: chart.figure,
          });
        } else {
          chartPanels.push({
            id: chart.id || chart.chart_id || `chart_${i}`,
            type: chart.type || chart.chart_type,
            title: chart.title,
            subtitle: chart.description,
            data: chart.data,
            figure: chart.figure,
            config: {
              x_axis: chart.x_axis,
              y_axis: chart.y_axis,
            },
          });
        }
      });
    }
    
    return {
      kpis: kpiPanels,
      charts: chartPanels,
      insights: dashboard.rawInsights || [],
      title: dashboard.title || dashboard.dashboard?.title || 'Analytics Dashboard',
    };
  }, [dashboard]);
  
  // Icon map for KPIs
  const kpiIcons = [FiDollarSign, FiUsers, FiShoppingCart, FiPackage];

  // Loading state
  if (isLoading) {
    return (
      <div 
        className="h-screen w-full flex items-center justify-center"
        style={{ backgroundColor: POWER_BI_COLORS.bgPrimary }}
      >
        <div className="text-center">
          <div 
            className="w-16 h-16 border-4 rounded-full animate-spin mx-auto mb-4"
            style={{ 
              borderColor: POWER_BI_COLORS.border,
              borderTopColor: POWER_BI_COLORS.blue,
            }}
          />
          <p style={{ color: POWER_BI_COLORS.textSecondary }}>
            Generating dashboard...
          </p>
        </div>
      </div>
    );
  }

  // Empty state
  if (!dashboard || charts.length === 0) {
    return (
      <div 
        className="h-screen w-full flex items-center justify-center"
        style={{ backgroundColor: POWER_BI_COLORS.bgPrimary }}
      >
        <div className="text-center max-w-md px-6">
          <div 
            className="w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center"
            style={{ backgroundColor: POWER_BI_COLORS.bgSecondary }}
          >
            <FiGrid className="text-4xl" style={{ color: POWER_BI_COLORS.textMuted }} />
          </div>
          <h2 
            className="text-2xl font-semibold mb-3"
            style={{ color: POWER_BI_COLORS.textPrimary }}
          >
            No Dashboard Data
          </h2>
          <p 
            className="mb-6"
            style={{ color: POWER_BI_COLORS.textSecondary }}
          >
            Upload a dataset and let AI generate insights and visualizations automatically.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/chat')}
              className="px-5 py-2.5 rounded-lg font-medium transition-colors"
              style={{ backgroundColor: POWER_BI_COLORS.blue, color: '#fff' }}
            >
              Go to Chat
            </button>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="px-5 py-2.5 rounded-lg font-medium transition-colors"
                style={{ 
                  backgroundColor: POWER_BI_COLORS.bgSecondary, 
                  color: POWER_BI_COLORS.textPrimary,
                  border: `1px solid ${POWER_BI_COLORS.border}`,
                }}
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="h-screen w-full flex flex-col overflow-hidden"
      style={{ backgroundColor: POWER_BI_COLORS.bgPrimary }}
    >
      {/* ================================================================== */}
      {/* HEADER BAR */}
      {/* ================================================================== */}
      <header 
        className="flex-shrink-0 px-4 py-3 flex items-center justify-between"
        style={{ 
          backgroundColor: POWER_BI_COLORS.bgSecondary,
          borderBottom: `1px solid ${POWER_BI_COLORS.border}`,
        }}
      >
        {/* Left: Back + Title */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/chat')}
            className="p-2 rounded-lg transition-colors hover:bg-gray-700/30"
            style={{ color: POWER_BI_COLORS.textSecondary }}
          >
            <FiArrowLeft className="text-xl" />
          </button>
          
          <div className="flex items-center gap-3">
            <div 
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: 'rgba(17, 141, 255, 0.15)' }}
            >
              <HiSparkles className="text-lg" style={{ color: POWER_BI_COLORS.blue }} />
            </div>
            <div>
              <h1 
                className="text-base font-semibold"
                style={{ color: POWER_BI_COLORS.textPrimary }}
              >
                {title}
              </h1>
              <p 
                className="text-xs"
                style={{ color: POWER_BI_COLORS.textMuted }}
              >
                {charts.length} visualizations • {kpis.length} KPIs
              </p>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 rounded-lg transition-colors hover:bg-gray-700/30 flex items-center gap-2"
            style={{ 
              color: showFilters ? POWER_BI_COLORS.blue : POWER_BI_COLORS.textSecondary,
            }}
          >
            <FiFilter className="text-lg" />
            <span className="text-sm hidden md:inline">Filters</span>
          </button>
          
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg transition-colors hover:bg-gray-700/30"
            style={{ color: POWER_BI_COLORS.textSecondary }}
            title="Refresh"
          >
            <FiRefreshCw className="text-lg" />
          </button>
          
          <button
            onClick={onExport}
            className="p-2 rounded-lg transition-colors hover:bg-gray-700/30"
            style={{ color: POWER_BI_COLORS.textSecondary }}
            title="Export"
          >
            <FiDownload className="text-lg" />
          </button>
          
          <button
            className="p-2 rounded-lg transition-colors hover:bg-gray-700/30"
            style={{ color: POWER_BI_COLORS.textSecondary }}
            title="Share"
          >
            <FiShare2 className="text-lg" />
          </button>
        </div>
      </header>

      {/* ================================================================== */}
      {/* MAIN CONTENT */}
      {/* ================================================================== */}
      <main className="flex-1 overflow-auto p-4">
        <div className="max-w-[1800px] mx-auto space-y-4">
          
          {/* KPI Cards Row */}
          {kpis.length > 0 && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {kpis.slice(0, 4).map((kpi, index) => (
                <KpiCard
                  key={kpi.id || index}
                  title={kpi.title || `Metric ${index + 1}`}
                  value={kpi.value || kpi.data?.[0]?.[Object.keys(kpi.data?.[0] || {})[0]]}
                  icon={kpiIcons[index % kpiIcons.length]}
                  colorIndex={index}
                />
              ))}
            </div>
          )}

          {/* Charts Grid */}
          <div 
            className="grid gap-4"
            style={{
              gridTemplateColumns: 'repeat(12, 1fr)',
              gridAutoRows: 'minmax(280px, auto)',
            }}
          >
            {charts.map((chart, index) => {
              // Determine grid size based on chart type
              const chartType = chart.type?.toLowerCase() || 'bar';
              let colSpan = 6;
              let rowSpan = 1;
              
              if (chartType === 'pie' || chartType === 'donut') {
                colSpan = 4;
              } else if (chartType === 'table' || chartType === 'heatmap') {
                colSpan = 6;
              } else if (index === 0 && charts.length > 2) {
                colSpan = 8; // First chart larger
              }
              
              return (
                <div
                  key={chart.id || index}
                  style={{
                    gridColumn: `span ${colSpan}`,
                    gridRow: `span ${rowSpan}`,
                  }}
                >
                  <ChartPanel title={chart.title} subtitle={chart.subtitle}>
                    <ChartRenderer panel={chart} />
                  </ChartPanel>
                </div>
              );
            })}
          </div>

          {/* Insights Section */}
          {insights.length > 0 && (
            <InsightsPanel insights={insights} />
          )}
        </div>
      </main>
    </div>
  );
};

export default PowerBIDashboard;
