/**
 * Analytics Page - Power BI-style analytics dashboard
 * 
 * Features:
 * - Full-screen 100vh dashboard
 * - Fetches dashboard data from backend
 * - Supports both new generation and loading existing dashboard
 * - Navigation from chat or direct access
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '../firebase';
import { AnalyticsDashboard } from '../components/analytics';
import { apiPost } from '../lib/api';

const Analytics = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasGenerated = useRef(false);

  // State
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  
  // Session info from navigation state or localStorage
  const [sessionId, setSessionId] = useState('');
  const [datasetId, setDatasetId] = useState('');

  // Auth check
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (!user) {
        navigate('/login');
      }
    });
    return () => unsubscribe();
  }, [navigate]);

  // Load session from location state or localStorage
  useEffect(() => {
    const stateSessionId = location.state?.sessionId;
    const stateDatasetId = location.state?.datasetId;
    const storedSessionId = localStorage.getItem('chatSessionId');
    const storedDatasetId = localStorage.getItem('datasetId');

    setSessionId(stateSessionId || storedSessionId || '');
    setDatasetId(stateDatasetId || storedDatasetId || '');
  }, [location.state]);

  // Generate dashboard when session is available
  useEffect(() => {
    if (sessionId && !hasGenerated.current) {
      hasGenerated.current = true;
      generateDashboard();
    }
  }, [sessionId]);

  // Generate dashboard from backend
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
        const errorMessage = errorData.detail || `Server error: ${response.status}`;
        
        // If 403 (ownership issue), clear stale session data and redirect
        if (response.status === 403) {
          console.warn('Session ownership issue - clearing stale session data');
          localStorage.removeItem('chatSessionId');
          localStorage.removeItem('datasetId');
          localStorage.removeItem('datasetGridfsId');
          localStorage.removeItem('datasetName');
          throw new Error('Session expired. Please upload your dataset again.');
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (data.status === 'error') {
        throw new Error(data.message || 'Failed to generate dashboard');
      }

      // Transform backend response to dashboard format
      const transformedDashboard = transformDashboardData(data);
      setDashboard(transformedDashboard);

    } catch (err) {
      console.error('Dashboard generation error:', err);
      setError(err.message || 'Failed to generate dashboard');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, datasetId, location.state?.prompt]);

  // Refresh handler
  const handleRefresh = useCallback(() => {
    hasGenerated.current = false;
    setDashboard(null);
    generateDashboard();
  }, [generateDashboard]);

  // Export handler (placeholder for future implementation)
  const handleExport = useCallback(() => {
    // TODO: Implement export functionality
    console.log('Export dashboard');
  }, []);

  // Error state
  if (error && !isLoading) {
    return (
      <div className="h-screen w-full bg-slate-950 flex items-center justify-center">
        <div className="text-center max-w-md p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-rose-500/20 flex items-center justify-center">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Dashboard Error
          </h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/chat')}
              className="px-4 py-2 rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition-colors"
            >
              Go to Chat
            </button>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AnalyticsDashboard
      dashboard={dashboard}
      isLoading={isLoading}
      onRefresh={handleRefresh}
      onExport={handleExport}
    />
  );
};

/**
 * Transform backend dashboard response to frontend format
 * 
 * Backend returns:
 * {
 *   status: "success",
 *   dashboard: { dashboard_id, title, charts: [...] },
 *   insights: [...]
 * }
 * 
 * Frontend expects:
 * {
 *   title, description, layout, panels: [...]
 * }
 */
function transformDashboardData(data) {
  const backendDashboard = data.dashboard || {};
  const charts = backendDashboard.charts || [];
  const insights = data.insights || [];

  // Calculate panel layouts automatically
  // Row 0: KPIs (if any)
  // Rows 1+: Charts
  let currentRow = 0;
  let currentCol = 0;
  const panels = [];

  // First pass: identify KPIs and place them in row 0
  // Backend returns chart.type, but also check chart_type for compatibility
  const kpiCharts = charts.filter(c => (c.type || c.chart_type) === 'kpi');
  const nonKpiCharts = charts.filter(c => (c.type || c.chart_type) !== 'kpi');

  // Add KPIs to top row (max 4, each 3 columns wide)
  kpiCharts.slice(0, 4).forEach((chart, index) => {
    panels.push({
      id: chart.id || chart.chart_id || `kpi_${index}`,
      type: 'kpi',
      title: chart.title,
      subtitle: chart.description,
      figure: chart.figure,
      data: chart.data,
      config: {
        x_axis: chart.x_axis,
        y_axis: chart.y_axis,
        aggregation: chart.aggregation,
      },
      layout: {
        x: index * 3,
        y: 0,
        w: 3,
        h: 1,
      },
    });
  });

  // Move to next row if we had KPIs
  if (kpiCharts.length > 0) {
    currentRow = 1;
  }

  // Add non-KPI charts
  nonKpiCharts.forEach((chart, index) => {
    const chartType = (chart.type || chart.chart_type)?.toLowerCase() || 'bar';
    
    // Determine panel size based on chart type
    let width = 6; // Default half-width
    let height = 3; // Default 3 rows

    if (chartType === 'pie') {
      width = 4;
      height = 3;
    } else if (chartType === 'histogram') {
      width = 6;
      height = 3;
    } else if (chartType === 'scatter' || chartType === 'scatter_plot') {
      width = 6;
      height = 3;
    } else if (chartType === 'heatmap' || chartType === 'correlation_heatmap') {
      width = 6;
      height = 3;
    } else if (chartType === 'table') {
      width = 12;
      height = 2;
    }

    // Check if we need to wrap to next row
    if (currentCol + width > 12) {
      currentCol = 0;
      currentRow += height;
    }

    panels.push({
      id: chart.id || chart.chart_id || `chart_${index}`,
      type: chartType,
      title: chart.title,
      subtitle: chart.description,
      figure: chart.figure,
      data: chart.data,
      config: {
        x_axis: chart.x_axis,
        y_axis: chart.y_axis,
        aggregation: chart.aggregation,
      },
      layout: {
        x: currentCol,
        y: currentRow,
        w: width,
        h: height,
      },
    });

    currentCol += width;
    if (currentCol >= 12) {
      currentCol = 0;
      currentRow += height;
    }
  });

  // Add insights as a panel if present
  if (insights.length > 0) {
    // Check space for insights panel
    if (currentCol !== 0) {
      currentRow += 3;
      currentCol = 0;
    }

    panels.push({
      id: 'insights_panel',
      type: 'insights',
      title: 'Key Insights',
      data: insights,
      layout: {
        x: 0,
        y: currentRow,
        w: 12,
        h: 1,
      },
    });
  }

  return {
    title: backendDashboard.title || 'Analytics Dashboard',
    description: backendDashboard.description,
    layout: {
      columns: 12,
      rowHeight: 100,
      gap: 16,
    },
    panels,
    rawInsights: insights,
  };
}

export default Analytics;
