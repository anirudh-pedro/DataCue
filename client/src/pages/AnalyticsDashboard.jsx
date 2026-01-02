/**
 * Modern Analytics Dashboard - Professional, Responsive, Interactive
 * 
 * Features:
 * - Glassmorphism design with gradient backgrounds
 * - Fully responsive grid layout
 * - Interactive chart controls and filters
 * - Real-time data updates
 * - Export and sharing capabilities
 * - Dark mode optimized
 * - Smooth animations and transitions
 */

import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '../firebase';
import { apiPost, apiGet } from '../lib/api';
import Plot from 'react-plotly.js';
import { 
  FiArrowLeft, 
  FiRefreshCw, 
  FiDownload, 
  FiShare2, 
  FiMaximize2,
  FiFilter,
  FiCalendar,
  FiTrendingUp,
  FiTrendingDown,
  FiBarChart2,
  FiPieChart,
  FiActivity,
  FiDollarSign,
  FiUsers,
  FiShoppingCart,
  FiPackage,
  FiGrid,
  FiLayout,
  FiX,
  FiChevronDown,
  FiSearch,
  FiSettings,
  FiZap,
  FiStar,
  FiHeart
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

// ============================================================================
// DESIGN SYSTEM
// ============================================================================
const theme = {
  colors: {
    // Gradients
    gradientPurple: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    gradientBlue: 'linear-gradient(135deg, #667eea 0%, #37cdff 100%)',
    gradientGreen: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    gradientOrange: 'linear-gradient(135deg, #f77062 0%, #fe5196 100%)',
    gradientYellow: 'linear-gradient(135deg, #f2b900 0%, #feb47b 100%)',
    
    // Solid colors
    primary: '#667eea',
    secondary: '#764ba2',
    success: '#38ef7d',
    warning: '#feb47b',
    danger: '#fe5196',
    
    // Chart colors
    chart: ['#667eea', '#37cdff', '#38ef7d', '#feb47b', '#fe5196', '#764ba2', '#11998e', '#f77062'],
    
    // Background
    bg: {
      primary: '#0a0e27',
      secondary: '#151932',
      tertiary: '#1e2238',
      card: 'rgba(30, 34, 56, 0.8)',
      glass: 'rgba(255, 255, 255, 0.05)',
    },
    
    // Text
    text: {
      primary: '#ffffff',
      secondary: '#a0aec0',
      muted: '#718096',
    },
    
    // Border
    border: 'rgba(255, 255, 255, 0.1)',
  },
  
  shadows: {
    sm: '0 2px 4px rgba(0, 0, 0, 0.3)',
    md: '0 4px 12px rgba(0, 0, 0, 0.4)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.5)',
    glow: '0 0 20px rgba(102, 126, 234, 0.4)',
  },
};

// ============================================================================
// KPI CARD COMPONENT
// ============================================================================
const KpiCard = ({ title, value, change, changeType, icon: Icon, gradient, loading }) => {
  const formatValue = (val) => {
    if (val === null || val === undefined) return '—';
    const num = typeof val === 'string' ? parseFloat(val.replace(/[,$]/g, '')) : val;
    if (isNaN(num)) return val;
    if (Math.abs(num) >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (Math.abs(num) >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const TrendIcon = changeType === 'up' ? FiTrendingUp : changeType === 'down' ? FiTrendingDown : null;
  const trendColor = changeType === 'up' ? theme.colors.success : changeType === 'down' ? theme.colors.danger : theme.colors.text.muted;

  return (
    <div 
      className="group relative rounded-2xl p-6 backdrop-blur-xl border transition-all duration-300 hover:scale-[1.02] hover:shadow-xl cursor-pointer overflow-hidden"
      style={{
        background: theme.colors.bg.card,
        borderColor: theme.colors.border,
        boxShadow: theme.shadows.md,
      }}
    >
      {/* Gradient overlay on hover */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-300"
        style={{ background: gradient }}
      />
      
      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110"
            style={{ background: gradient }}
          >
            {Icon && <Icon className="text-white text-xl" />}
          </div>
          
          {change !== undefined && TrendIcon && (
            <div 
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-semibold"
              style={{ 
                backgroundColor: `${trendColor}20`,
                color: trendColor 
              }}
            >
              <TrendIcon className="text-xs" />
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        
        {/* Title */}
        <div className="text-sm font-medium mb-2" style={{ color: theme.colors.text.secondary }}>
          {title}
        </div>
        
        {/* Value */}
        <div className="text-3xl font-bold" style={{ color: theme.colors.text.primary }}>
          {loading ? (
            <div className="h-9 w-32 bg-gray-700/30 rounded animate-pulse" />
          ) : (
            formatValue(value)
          )}
        </div>
      </div>
      
      {/* Sparkle effect */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <HiSparkles className="text-white/20" />
      </div>
    </div>
  );
};

// ============================================================================
// CHART CARD COMPONENT
// ============================================================================
const ChartCard = ({ title, subtitle, children, onExpand, loading }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div 
      className="relative rounded-2xl backdrop-blur-xl border transition-all duration-300 hover:shadow-xl overflow-hidden flex flex-col h-full"
      style={{
        background: theme.colors.bg.card,
        borderColor: theme.colors.border,
        boxShadow: theme.shadows.md,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-center justify-between flex-shrink-0">
        <div className="min-w-0 flex-1">
          <h3 
            className="text-base font-semibold truncate"
            style={{ color: theme.colors.text.primary }}
          >
            {title}
          </h3>
          {subtitle && (
            <p 
              className="text-xs truncate mt-1"
              style={{ color: theme.colors.text.muted }}
            >
              {subtitle}
            </p>
          )}
        </div>
        
        {/* Action buttons - show on hover */}
        <div className={`flex items-center gap-2 transition-opacity duration-200 ${isHovered ? 'opacity-100' : 'opacity-0'}`}>
          {onExpand && (
            <button 
              onClick={onExpand}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              style={{ color: theme.colors.text.secondary }}
            >
              <FiMaximize2 className="text-sm" />
            </button>
          )}
        </div>
      </div>
      
      {/* Chart Content */}
      <div className="flex-1 px-4 pb-4 min-h-0">
        {loading ? (
          <div className="h-full w-full flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-2"
                style={{ borderColor: theme.colors.primary, borderRightColor: 'transparent' }}
              />
              <p className="text-sm" style={{ color: theme.colors.text.muted }}>Loading chart...</p>
            </div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================
const AnalyticsDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // State
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [datasetId, setDatasetId] = useState(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  const hasGenerated = useRef(false);

  // Auth check
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (!user) {
        navigate('/login');
      }
    });
    return () => unsubscribe();
  }, [navigate]);

  // Load session from state or localStorage
  useEffect(() => {
    const stateSessionId = location.state?.sessionId;
    const stateDatasetId = location.state?.datasetId;
    const storedSessionId = localStorage.getItem('sessionId') || localStorage.getItem('chatSessionId');
    const storedDatasetId = localStorage.getItem('datasetId');

    const finalSessionId = stateSessionId || storedSessionId || '';
    const finalDatasetId = stateDatasetId || storedDatasetId || '';
    
    setSessionId(finalSessionId);
    setDatasetId(finalDatasetId);
    
    if (finalSessionId && !localStorage.getItem('sessionId')) {
      localStorage.setItem('sessionId', finalSessionId);
    }
  }, [location.state]);

  // Generate dashboard
  useEffect(() => {
    if (sessionId === null) return;
    
    if (sessionId && !hasGenerated.current) {
      hasGenerated.current = true;
      generateDashboard();
    } else if (!sessionId) {
      setError('No session ID available. Please upload a dataset first.');
      setIsLoading(false);
    }
  }, [sessionId]);

  const generateDashboard = useCallback(async () => {
    if (!sessionId) {
      setError('No session ID available. Please upload a dataset first.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        session_id: sessionId,
        user_prompt: location.state?.prompt || null,
      };

      if (datasetId) {
        payload.dataset_id = datasetId;
      }

      const response = await apiPost('/dashboard/generate', payload);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'error') {
        throw new Error(data.message || 'Failed to generate dashboard');
      }

      const transformedDashboard = transformDashboardData(data);
      setDashboard(transformedDashboard);

    } catch (err) {
      console.error('Dashboard generation error:', err);
      setError(err.message || 'Failed to generate dashboard');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, datasetId, location.state?.prompt]);

  const handleRefresh = useCallback(() => {
    hasGenerated.current = false;
    setDashboard(null);
    generateDashboard();
  }, [generateDashboard]);

  const handleExport = useCallback(() => {
    console.log('Export dashboard');
    // TODO: Implement export
  }, []);

  // Plotly theme
  const plotlyTheme = useMemo(() => ({
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      color: theme.colors.text.secondary,
      size: 12,
    },
    margin: { t: 30, r: 30, b: 50, l: 60 },
    xaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      zerolinecolor: 'rgba(255, 255, 255, 0.1)',
      tickfont: { size: 11, color: theme.colors.text.muted },
      linecolor: 'rgba(255, 255, 255, 0.1)',
    },
    yaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      zerolinecolor: 'rgba(255, 255, 255, 0.1)',
      tickfont: { size: 11, color: theme.colors.text.muted },
      linecolor: 'rgba(255, 255, 255, 0.1)',
    },
    colorway: theme.colors.chart,
    hoverlabel: {
      bgcolor: theme.colors.bg.tertiary,
      bordercolor: theme.colors.border,
      font: { color: theme.colors.text.primary, size: 13 },
    },
    legend: {
      font: { color: theme.colors.text.secondary, size: 11 },
      bgcolor: 'transparent',
      orientation: 'h',
      y: -0.15,
      x: 0.5,
      xanchor: 'center',
    },
  }), []);

  // Error state
  if (error && !isLoading) {
    return (
      <div 
        className="min-h-screen w-full flex items-center justify-center p-6"
        style={{ 
          background: `radial-gradient(circle at 50% 0%, ${theme.colors.bg.secondary} 0%, ${theme.colors.bg.primary} 100%)`
        }}
      >
        <div className="text-center max-w-md">
          <div 
            className="w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center"
            style={{ background: theme.colors.gradientOrange }}
          >
            <span className="text-4xl">⚠️</span>
          </div>
          <h2 className="text-2xl font-bold mb-3" style={{ color: theme.colors.text.primary }}>
            Dashboard Error
          </h2>
          <p className="text-base mb-8" style={{ color: theme.colors.text.secondary }}>
            {error}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/chat')}
              className="px-6 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105"
              style={{ 
                backgroundColor: theme.colors.bg.tertiary,
                color: theme.colors.text.primary 
              }}
            >
              Go to Chat
            </button>
            <button
              onClick={handleRefresh}
              className="px-6 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105"
              style={{ 
                background: theme.colors.gradientBlue,
                color: 'white',
                boxShadow: theme.shadows.glow
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div 
        className="min-h-screen w-full flex items-center justify-center"
        style={{ 
          background: `radial-gradient(circle at 50% 0%, ${theme.colors.bg.secondary} 0%, ${theme.colors.bg.primary} 100%)`
        }}
      >
        <div className="text-center">
          <div 
            className="inline-block h-16 w-16 animate-spin rounded-full border-4 border-solid mb-4"
            style={{ 
              borderColor: theme.colors.primary,
              borderRightColor: 'transparent'
            }}
          />
          <p className="text-lg font-medium" style={{ color: theme.colors.text.secondary }}>
            Generating your dashboard...
          </p>
          <p className="text-sm mt-2" style={{ color: theme.colors.text.muted }}>
            This may take a few moments
          </p>
        </div>
      </div>
    );
  }

  // Render dashboard
  const { kpis = [], charts = [], insights = [] } = dashboard || {};

  return (
    <div 
      className="min-h-screen w-full"
      style={{ 
        background: `radial-gradient(circle at 50% 0%, ${theme.colors.bg.secondary} 0%, ${theme.colors.bg.primary} 100%)`
      }}
    >
      {/* Top Navigation Bar */}
      <div 
        className="sticky top-0 z-50 backdrop-blur-xl border-b"
        style={{
          backgroundColor: `${theme.colors.bg.card}cc`,
          borderColor: theme.colors.border,
          boxShadow: theme.shadows.sm,
        }}
      >
        <div className="max-w-[1920px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Back button + Title */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/chat')}
                className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                style={{ color: theme.colors.text.secondary }}
              >
                <FiArrowLeft className="text-xl" />
              </button>
              <div>
                <h1 
                  className="text-xl font-bold flex items-center gap-2"
                  style={{ color: theme.colors.text.primary }}
                >
                  <HiSparkles style={{ color: theme.colors.primary }} />
                  Analytics Dashboard
                </h1>
                <p className="text-sm mt-0.5" style={{ color: theme.colors.text.muted }}>
                  Real-time data insights and visualizations
                </p>
              </div>
            </div>
            
            {/* Right: Actions */}
            <div className="flex items-center gap-3">
              {/* Search */}
              <div className="relative hidden md:block">
                <FiSearch 
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-base"
                  style={{ color: theme.colors.text.muted }}
                />
                <input
                  type="text"
                  placeholder="Search charts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 rounded-xl border focus:outline-none focus:ring-2 transition-all"
                  style={{
                    backgroundColor: theme.colors.bg.glass,
                    borderColor: theme.colors.border,
                    color: theme.colors.text.primary,
                  }}
                />
              </div>
              
              {/* Time Range Filter */}
              <button
                className="px-4 py-2 rounded-xl flex items-center gap-2 hover:bg-white/10 transition-colors"
                style={{ color: theme.colors.text.secondary }}
              >
                <FiCalendar />
                <span className="hidden sm:inline">Last 30 days</span>
                <FiChevronDown className="text-xs" />
              </button>
              
              {/* Filter Toggle */}
              <button
                onClick={() => setFilterOpen(!filterOpen)}
                className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                style={{ color: theme.colors.text.secondary }}
              >
                <FiFilter className="text-lg" />
              </button>
              
              {/* Refresh */}
              <button
                onClick={handleRefresh}
                className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                style={{ color: theme.colors.text.secondary }}
                disabled={isLoading}
              >
                <FiRefreshCw className={`text-lg ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              
              {/* Export */}
              <button
                onClick={handleExport}
                className="px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all duration-200 hover:scale-105"
                style={{ 
                  background: theme.colors.gradientBlue,
                  color: 'white',
                  boxShadow: theme.shadows.glow
                }}
              >
                <FiDownload />
                <span className="hidden sm:inline">Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1920px] mx-auto px-6 py-8">
        {/* KPI Cards */}
        {kpis.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {kpis.map((kpi, index) => (
              <KpiCard
                key={kpi.id || index}
                title={kpi.title}
                value={kpi.value}
                change={kpi.change}
                changeType={kpi.changeType}
                icon={getIconForKpi(kpi.title)}
                gradient={theme.colors.chart[index % theme.colors.chart.length]}
                loading={isLoading}
              />
            ))}
          </div>
        )}

        {/* Charts Section - Chart LEFT, Description RIGHT */}
        {charts.length > 0 && (
          <div className="space-y-6 mb-8">
            {charts.map((chart, index) => (
              <div
                key={chart.id || index}
                className="rounded-2xl p-6 backdrop-blur-xl border transition-all duration-300 hover:shadow-xl"
                style={{
                  background: theme.colors.bg.card,
                  borderColor: theme.colors.border,
                  boxShadow: theme.shadows.md,
                }}
              >
                {/* Chart Title */}
                <h3 
                  className="text-lg font-semibold mb-4"
                  style={{ color: theme.colors.text.primary }}
                >
                  {chart.title}
                </h3>
                
                {/* Chart Content: LEFT = Chart, RIGHT = Description */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* LEFT: Chart (2/3 width) */}
                  <div className="lg:col-span-2">
                    {chart.figure && (
                      <Plot
                        data={chart.figure.data}
                        layout={{
                          ...plotlyTheme,
                          ...chart.figure.layout,
                          autosize: true,
                          height: 350,
                          margin: { t: 20, r: 20, b: 60, l: 60 },
                        }}
                        config={{
                          responsive: true,
                          displayModeBar: true,
                          displaylogo: false,
                          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                        }}
                        style={{ width: '100%', height: '350px' }}
                        useResizeHandler
                      />
                    )}
                  </div>
                  
                  {/* RIGHT: Description (1/3 width) */}
                  <div 
                    className="lg:col-span-1 rounded-xl p-5 flex flex-col justify-center"
                    style={{
                      backgroundColor: theme.colors.bg.glass,
                      borderColor: theme.colors.border,
                      border: '1px solid',
                    }}
                  >
                    {/* Chart Type Badge */}
                    <div className="mb-4">
                      <span 
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
                        style={{
                          background: theme.colors.gradientPurple,
                          color: '#fff',
                        }}
                      >
                        <FiBarChart2 />
                        {chart.type || 'Chart'}
                      </span>
                    </div>
                    
                    {/* Description */}
                    <p 
                      className="text-sm leading-relaxed mb-4"
                      style={{ color: theme.colors.text.secondary }}
                    >
                      {chart.subtitle || chart.description || 'Data visualization showing key metrics and trends.'}
                    </p>
                    
                    {/* Chart Stats */}
                    <div className="space-y-2 mt-auto">
                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: theme.colors.text.muted }}>Data Points</span>
                        <span 
                          className="font-semibold"
                          style={{ color: theme.colors.text.primary }}
                        >
                          {chart.figure?.data?.[0]?.x?.length || chart.figure?.data?.[0]?.values?.length || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: theme.colors.text.muted }}>Chart ID</span>
                        <span 
                          className="font-mono font-semibold"
                          style={{ color: theme.colors.text.primary }}
                        >
                          {(chart.id || index).toString().slice(0, 8)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Insights Panel */}
        {insights.length > 0 && (
          <div 
            className="rounded-2xl p-6 backdrop-blur-xl border"
            style={{
              background: theme.colors.bg.card,
              borderColor: theme.colors.border,
              boxShadow: theme.shadows.md,
            }}
          >
            <h3 
              className="text-lg font-semibold mb-4 flex items-center gap-2"
              style={{ color: theme.colors.text.primary }}
            >
              <FiZap style={{ color: theme.colors.warning }} />
              Key Insights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {insights.map((insight, index) => (
                <div
                  key={index}
                  className="p-4 rounded-xl border"
                  style={{
                    backgroundColor: theme.colors.bg.glass,
                    borderColor: theme.colors.border,
                  }}
                >
                  <p className="text-sm" style={{ color: theme.colors.text.secondary }}>
                    {insight.text || insight}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function transformDashboardData(data) {
  const backendDashboard = data.dashboard || {};
  const charts = backendDashboard.charts || [];
  const insights = data.insights || [];

  // Extract KPIs
  const kpis = charts
    .filter(c => (c.type || c.chart_type) === 'kpi')
    .map(kpi => ({
      id: kpi.id || kpi.chart_id,
      title: kpi.title,
      value: kpi.data?.value || kpi.value,
      change: kpi.data?.change,
      changeType: kpi.data?.changeType || (kpi.data?.change > 0 ? 'up' : 'down'),
    }));

  // Extract non-KPI charts
  const chartData = charts
    .filter(c => (c.type || c.chart_type) !== 'kpi')
    .map(chart => ({
      id: chart.id || chart.chart_id,
      type: (chart.type || chart.chart_type)?.toLowerCase(),
      title: chart.title,
      subtitle: chart.description,
      figure: chart.figure,
      data: chart.data,
    }));

  return {
    title: backendDashboard.title || 'Analytics Dashboard',
    kpis,
    charts: chartData,
    insights,
  };
}

function getIconForKpi(title) {
  const lower = title.toLowerCase();
  if (lower.includes('revenue') || lower.includes('sales') || lower.includes('profit')) return FiDollarSign;
  if (lower.includes('user') || lower.includes('customer')) return FiUsers;
  if (lower.includes('order') || lower.includes('transaction')) return FiShoppingCart;
  if (lower.includes('product') || lower.includes('item')) return FiPackage;
  if (lower.includes('rate') || lower.includes('growth')) return FiTrendingUp;
  return FiBarChart2;
}

export default AnalyticsDashboard;
