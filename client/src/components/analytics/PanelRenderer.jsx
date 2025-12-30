/**
 * PanelRenderer - Routes panel type to appropriate visualization component
 * 
 * Supported types:
 * - kpi: Key Performance Indicator card
 * - bar / grouped_bar: Bar chart
 * - line / time_series: Line chart
 * - pie: Pie/donut chart
 * - scatter / scatter_plot: Scatter plot
 * - histogram: Histogram
 * - table: Data table
 * - heatmap / correlation_heatmap: Heatmap
 * - box / box_plot: Box plot
 * - insights: Key insights display
 */

import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import KpiPanel from './KpiPanel';
import DataTable from './DataTable';
import InsightsPanel from './InsightsPanel';

// Professional LIGHT theme config for Plotly charts (Power BI style)
const CHART_THEME = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: {
    family: 'Segoe UI, Inter, -apple-system, BlinkMacSystemFont, Roboto, sans-serif',
    color: '#374151',
    size: 11,
  },
  margin: { t: 10, r: 15, b: 40, l: 50 },
  xaxis: {
    gridcolor: 'rgba(229, 231, 235, 0.8)',
    zerolinecolor: 'rgba(209, 213, 219, 0.8)',
    tickfont: { size: 10, color: '#6b7280' },
    title: { font: { size: 11, color: '#374151' } },
    linecolor: '#e5e7eb',
    showgrid: true,
  },
  yaxis: {
    gridcolor: 'rgba(229, 231, 235, 0.8)',
    zerolinecolor: 'rgba(209, 213, 219, 0.8)',
    tickfont: { size: 10, color: '#6b7280' },
    title: { font: { size: 11, color: '#374151' } },
    linecolor: '#e5e7eb',
    showgrid: true,
  },
  // Power BI-inspired color palette
  colorway: [
    '#118DFF', // Primary Blue
    '#12239E', // Dark Blue
    '#E66C37', // Orange
    '#6B007B', // Purple
    '#E044A7', // Pink
    '#744EC2', // Violet
    '#D9B300', // Yellow
    '#D64550', // Red
    '#197278', // Teal
    '#1AAB40', // Green
    '#893B7F', // Magenta
    '#4E8542', // Forest
  ],
  hoverlabel: {
    bgcolor: '#ffffff',
    bordercolor: '#e5e7eb',
    font: { color: '#111827', size: 12, family: 'Segoe UI, sans-serif' },
  },
  legend: {
    font: { color: '#374151', size: 10 },
    bgcolor: 'rgba(255,255,255,0.9)',
    bordercolor: '#e5e7eb',
    borderwidth: 1,
    orientation: 'h',
    y: -0.15,
  },
  modebar: {
    bgcolor: 'transparent',
    color: '#9ca3af',
    activecolor: '#118DFF',
  },
};

const PanelRenderer = ({ panel }) => {
  const { type, data, config, figure } = panel;
  const chartType = type?.toLowerCase() || 'bar';

  // Memoize chart data normalization (must be before any early returns to satisfy React hooks rules)
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return null;
    }
    return data;
  }, [data]);

  // Handle KPI panels
  if (chartType === 'kpi') {
    return <KpiPanel panel={panel} />;
  }

  // Handle insights panels
  if (chartType === 'insights') {
    const insightsData = data || figure?.data;
    return <InsightsPanel insights={insightsData} />;
  }

  // Handle table panels
  if (chartType === 'table') {
    const tableData = data || figure?.data;
    return <DataTable data={tableData} />;
  }

  // If backend provided a Plotly figure, use it directly
  if (figure && figure.data && Array.isArray(figure.data)) {
    return (
      <Plot
        data={figure.data}
        layout={{
          ...CHART_THEME,
          ...(figure.layout || {}),
          autosize: true,
        }}
        config={{
          displayModeBar: false,
          responsive: true,
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    );
  }

  // Handle empty data (fallback for raw data charts)
  if (!chartData) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        No data available
      </div>
    );
  }

  // Build Plotly trace based on chart type (for raw data)
  const { traces, layout } = buildPlotlyConfig(chartType, chartData, config, panel);

  return (
    <Plot
      data={traces}
      layout={{
        ...CHART_THEME,
        ...layout,
        autosize: true,
      }}
      config={{
        displayModeBar: false,
        responsive: true,
      }}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler={true}
    />
  );
};

/**
 * Build Plotly configuration based on chart type
 */
function buildPlotlyConfig(chartType, data, config, panel) {
  const xAxis = config?.x_axis;
  const yAxis = config?.y_axis;

  switch (chartType) {
    case 'bar':
    case 'grouped_bar':
      return buildBarChart(data, xAxis, yAxis);

    case 'line':
    case 'time_series':
      return buildLineChart(data, xAxis, yAxis);

    case 'pie':
    case 'donut':
      return buildPieChart(data, xAxis, yAxis);

    case 'scatter':
    case 'scatter_plot':
      return buildScatterChart(data, xAxis, yAxis);

    case 'histogram':
      return buildHistogram(data, xAxis);

    case 'heatmap':
    case 'correlation_heatmap':
      return buildHeatmap(data, xAxis, yAxis);

    case 'box':
    case 'box_plot':
      return buildBoxPlot(data, xAxis, yAxis);

    default:
      return buildBarChart(data, xAxis, yAxis);
  }
}

function buildBarChart(data, xKey, yKey) {
  // Auto-detect keys if not provided
  const keys = Object.keys(data[0] || {});
  const x = xKey || keys[0];
  const y = yKey || keys[1] || keys[0];

  return {
    traces: [{
      type: 'bar',
      x: data.map(d => d[x]),
      y: data.map(d => d[y]),
      marker: {
        color: '#6366f1',
        line: { color: '#818cf8', width: 1 },
      },
      hovertemplate: `<b>%{x}</b><br>${y}: %{y:,.0f}<extra></extra>`,
    }],
    layout: {
      xaxis: { title: { text: x, standoff: 10 } },
      yaxis: { title: { text: y, standoff: 10 } },
      bargap: 0.3,
    },
  };
}

function buildLineChart(data, xKey, yKey) {
  const keys = Object.keys(data[0] || {});
  const x = xKey || keys[0];
  const y = yKey || keys[1] || keys[0];

  return {
    traces: [{
      type: 'scatter',
      mode: 'lines+markers',
      x: data.map(d => d[x]),
      y: data.map(d => d[y]),
      line: { color: '#8b5cf6', width: 2, shape: 'spline' },
      marker: { color: '#a855f7', size: 6 },
      fill: 'tozeroy',
      fillcolor: 'rgba(139, 92, 246, 0.1)',
      hovertemplate: `<b>%{x}</b><br>${y}: %{y:,.2f}<extra></extra>`,
    }],
    layout: {
      xaxis: { title: { text: x, standoff: 10 } },
      yaxis: { title: { text: y, standoff: 10 } },
    },
  };
}

function buildPieChart(data, labelKey, valueKey) {
  const keys = Object.keys(data[0] || {});
  const label = labelKey || keys[0];
  const value = valueKey || keys[1] || 'count';

  return {
    traces: [{
      type: 'pie',
      labels: data.map(d => d[label]),
      values: data.map(d => d[value] || d.count || 1),
      hole: 0.4,
      marker: {
        line: { color: '#0f172a', width: 2 },
      },
      textposition: 'inside',
      textinfo: 'percent',
      textfont: { size: 11, color: '#fff' },
      hovertemplate: '<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>',
    }],
    layout: {
      showlegend: true,
      legend: {
        orientation: 'h',
        y: -0.1,
        x: 0.5,
        xanchor: 'center',
        font: { size: 10 },
      },
      margin: { t: 10, r: 10, b: 30, l: 10 },
    },
  };
}

function buildScatterChart(data, xKey, yKey) {
  const keys = Object.keys(data[0] || {});
  const x = xKey || keys[0];
  const y = yKey || keys[1] || keys[0];

  return {
    traces: [{
      type: 'scatter',
      mode: 'markers',
      x: data.map(d => d[x]),
      y: data.map(d => d[y]),
      marker: {
        color: '#22c55e',
        size: 8,
        opacity: 0.7,
        line: { color: '#16a34a', width: 1 },
      },
      hovertemplate: `${x}: %{x}<br>${y}: %{y}<extra></extra>`,
    }],
    layout: {
      xaxis: { title: { text: x, standoff: 10 } },
      yaxis: { title: { text: y, standoff: 10 } },
    },
  };
}

function buildHistogram(data, xKey) {
  const keys = Object.keys(data[0] || {});
  const x = xKey || keys[0];

  return {
    traces: [{
      type: 'histogram',
      x: data.map(d => d[x]),
      marker: {
        color: '#06b6d4',
        line: { color: '#0e7490', width: 1 },
      },
      hovertemplate: '%{x}: %{y} items<extra></extra>',
    }],
    layout: {
      xaxis: { title: { text: x, standoff: 10 } },
      yaxis: { title: { text: 'Count', standoff: 10 } },
      bargap: 0.05,
    },
  };
}

function buildHeatmap(data, xKey, yKey) {
  // Heatmap expects a 2D array or specific format
  const keys = Object.keys(data[0] || {});
  
  // If data is already in z-matrix format
  if (data[0]?.z) {
    return {
      traces: [{
        type: 'heatmap',
        z: data.map(d => d.z),
        colorscale: 'Viridis',
      }],
      layout: {},
    };
  }

  // Try to build from raw data
  const x = xKey || keys[0];
  const y = yKey || keys[1];
  const value = keys[2] || 'value';

  return {
    traces: [{
      type: 'heatmap',
      x: [...new Set(data.map(d => d[x]))],
      y: [...new Set(data.map(d => d[y]))],
      z: data.map(d => d[value]),
      colorscale: 'Viridis',
    }],
    layout: {
      xaxis: { title: { text: x } },
      yaxis: { title: { text: y } },
    },
  };
}

function buildBoxPlot(data, xKey, yKey) {
  const keys = Object.keys(data[0] || {});
  const y = yKey || xKey || keys[0];

  return {
    traces: [{
      type: 'box',
      y: data.map(d => d[y]),
      marker: { color: '#f97316' },
      line: { color: '#ea580c' },
      hovertemplate: '%{y}<extra></extra>',
    }],
    layout: {
      yaxis: { title: { text: y, standoff: 10 } },
    },
  };
}

export default PanelRenderer;
