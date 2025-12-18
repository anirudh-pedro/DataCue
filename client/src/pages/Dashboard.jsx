import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import BarChart from '../components/charts/BarChart';
import LineChart from '../components/charts/LineChart';
import ScatterPlot from '../components/charts/ScatterPlot';
import Histogram from '../components/charts/Histogram';
import PieChart from '../components/charts/PieChart';
import Heatmap from '../components/charts/Heatmap';
import BoxPlot from '../components/charts/BoxPlot';
import PlotCard from '../components/charts/PlotCard';
import KpiCard from '../components/KpiCard';
import { HiSparkles } from 'react-icons/hi2';
import { FiArrowLeft, FiX } from 'react-icons/fi';
import { auth } from '../firebase';
import sessionManager from '../utils/sessionManager';
import { apiGet } from '../lib/api';

const chartRegistry = {
  bar: { component: BarChart, mode: 'plotly' },
  grouped_bar: { component: PlotCard, mode: 'figure' },
  line: { component: LineChart, mode: 'plotly' },
  time_series: { component: LineChart, mode: 'plotly' },
  scatter: { component: ScatterPlot, mode: 'plotly' },
  scatter_plot: { component: ScatterPlot, mode: 'plotly' },
  histogram: { component: Histogram, mode: 'plotly' },
  pie: { component: PieChart, mode: 'plotly' },
  heatmap: { component: Heatmap, mode: 'plotly' },
  correlation_heatmap: { component: Heatmap, mode: 'plotly' },
  box_plot: { component: BoxPlot, mode: 'plotly' },
  box: { component: BoxPlot, mode: 'plotly' },
  treemap: { component: PlotCard, mode: 'figure' },
  funnel: { component: PlotCard, mode: 'figure' },
  sankey: { component: PlotCard, mode: 'figure' },
  stacked_area: { component: PlotCard, mode: 'figure' },
  kpi: { component: KpiCard, mode: 'kpi' },
  default: { component: PlotCard, mode: 'figure' },
};

const integerFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

const formatInteger = (value) => {
  if (value === null || value === undefined) {
    return '—';
  }
  return integerFormatter.format(value);
};

const capitalize = (value) => {
  if (!value || typeof value !== 'string') {
    return '';
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
};

const ratingStyles = {
  excellent: 'border border-emerald-400/40 bg-emerald-500/20 text-emerald-200',
  good: 'border border-sky-400/40 bg-sky-500/20 text-sky-200',
  fair: 'border border-amber-400/40 bg-amber-500/20 text-amber-200',
  poor: 'border border-rose-400/40 bg-rose-500/20 text-rose-200',
};

const PRIMARY_CHART_LIMIT = 4;
const MAX_KPI_CARDS = 2;
const MAX_DATASET_INSIGHTS = 3;

const splitCsvLine = (line = '') => {
  const cells = [];
  let current = '';
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      const next = line[index + 1];
      if (next === '"') {
        current += '"';
        index += 1;
        continue;
      }
      inQuotes = !inQuotes;
      continue;
    }

    if (char === ',' && !inQuotes) {
      cells.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  cells.push(current.trim());
  return cells;
};

const parseCsvText = (text) => {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (!lines.length) {
    throw new Error('The CSV file is empty.');
  }

  const headers = splitCsvLine(lines[0]);
  if (!headers.length) {
    throw new Error('Unable to detect columns inside the CSV.');
  }

  const rows = lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    const record = {};
    headers.forEach((header, index) => {
      record[header] = values[index] ?? '';
    });
    return record;
  });

  if (!rows.length) {
    throw new Error('No data rows were found in the CSV file.');
  }

  return { headers, rows };
};

const parseNumericValue = (rawValue) => {
  if (rawValue === null || rawValue === undefined) {
    return Number.NaN;
  }
  const normalized = String(rawValue).replace(/,/g, '').trim();
  if (!normalized) {
    return Number.NaN;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
};

const isParsableDate = (value) => {
  if (!value) {
    return false;
  }
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp);
};

const inferColumnProfiles = (rows, headers) => {
  const profiles = {
    allColumns: headers,
    numeric: [],
    categorical: [],
    time: [],
  };

        <input
          type="file"
          accept=".csv,text/csv"
          ref={fileInputRef}
          className="hidden"
          onChange={handleLocalCsvUpload}
        />
  headers.forEach((header) => {
    const values = rows.map((row) => row[header]).filter((value) => value !== undefined && value !== null);
    if (!values.length) {
      profiles.categorical.push(header);
      return;
    }

    const numericCount = values.reduce((count, value) => {
      const parsed = parseNumericValue(value);
      return Number.isFinite(parsed) ? count + 1 : count;
    }, 0);

              <div className="mt-6 flex flex-col gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                  className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:border-slate-500"
                >
                  Build dashboard from CSV
                </button>
                <button
                  onClick={() => navigate('/chat')}
                  type="button"
                  className="rounded-xl bg-white px-5 py-2 text-sm font-medium text-[#0d1117] transition hover:bg-slate-200"
                >
                  Upload via conversational flow
                </button>
                {csvError ? renderCsvError() : null}
                <p className="text-xs text-slate-500">Accepted format: .csv up to 5MB.</p>
              </div>
    if (dateCount / values.length >= 0.6) {
      profiles.time.push(header);
      return;
    }

    profiles.categorical.push(header);
  });

  return profiles;
};

const aggregateByCategory = (rows, categoryColumn, valueColumn) => {
  const totals = new Map();
  rows.forEach((row) => {
    const category = row[categoryColumn] || 'Unknown';
    const value = parseNumericValue(row[valueColumn]);
    if (!Number.isFinite(value)) {
      return;
    }
    totals.set(category, (totals.get(category) ?? 0) + value);
  });
  return Array.from(totals.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12);
};

const createHistogramChart = (rows, column) => {
  const series = rows
    .map((row) => parseNumericValue(row[column]))
    .filter((value) => Number.isFinite(value));
  if (series.length < 5) {
    return null;
  }
  return {
    id: `hist-${column}`,
    type: 'histogram',
    title: `${column} distribution`,
    figure: {
      data: [
        {
          type: 'histogram',
          x: series,
          marker: { color: '#38bdf8' },
        },
      ],
      layout: {
        margin: { t: 40, r: 20, b: 40, l: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0' },
      },
    },
  };
};

const createBarChart = (rows, categoryColumn, valueColumn) => {
  const aggregated = aggregateByCategory(rows, categoryColumn, valueColumn);
  if (!aggregated.length) {
    return null;
  }
  const labels = aggregated.map(([label]) => label);
  const values = aggregated.map(([, value]) => value);
  return {
    id: `bar-${categoryColumn}`,
    type: 'bar',
    title: `${valueColumn} by ${categoryColumn}`,
    figure: {
      data: [
        {
          type: 'bar',
          x: labels,
          y: values,
          marker: { color: '#818cf8' },
        },
      ],
      layout: {
        margin: { t: 40, r: 20, b: 80, l: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0' },
      },
    },
  };
};

const createLineChart = (rows, timeColumn, valueColumn) => {
  const grouped = new Map();
  rows.forEach((row) => {
    const rawDate = row[timeColumn];
    if (!isParsableDate(rawDate)) {
      return;
    }
    const value = parseNumericValue(row[valueColumn]);
    if (!Number.isFinite(value)) {
      return;
    }
    const dateKey = new Date(rawDate).toISOString().split('T')[0];
    grouped.set(dateKey, (grouped.get(dateKey) ?? 0) + value);
  });

  if (!grouped.size) {
    return null;
  }

  const sortedEntries = Array.from(grouped.entries()).sort((a, b) => (a[0] > b[0] ? 1 : -1));
  return {
    id: `line-${valueColumn}`,
    type: 'line',
    title: `${valueColumn} over time`,
    figure: {
      data: [
        {
          type: 'scatter',
          mode: 'lines+markers',
          x: sortedEntries.map(([date]) => date),
          y: sortedEntries.map(([, value]) => value),
          line: { color: '#34d399', width: 3 },
          marker: { color: '#10b981' },
        },
      ],
      layout: {
        margin: { t: 40, r: 20, b: 40, l: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0' },
      },
    },
  };
};

const createScatterChart = (rows, xColumn, yColumn, colorColumn) => {
  const points = rows
    .map((row) => {
      const x = parseNumericValue(row[xColumn]);
      const y = parseNumericValue(row[yColumn]);
      if (!Number.isFinite(x) || !Number.isFinite(y)) {
        return null;
      }
      return {
        x,
        y,
        color: colorColumn ? row[colorColumn] : undefined,
      };
    })
    .filter(Boolean);

  if (points.length < 5) {
    return null;
  }

  return {
    id: `scatter-${xColumn}-${yColumn}`,
    type: 'scatter',
    title: `${yColumn} vs ${xColumn}`,
    figure: {
      data: [
        {
          type: 'scatter',
          mode: 'markers',
          x: points.map((point) => point.x),
          y: points.map((point) => point.y),
          marker: {
            color: points.map((point) => point.color || '#93c5fd'),
            size: 10,
            opacity: 0.8,
          },
        },
      ],
      layout: {
        margin: { t: 40, r: 40, b: 40, l: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0' },
      },
    },
  };
};

const generateChartsFromCsv = (rows, profiles) => {
  const charts = [];

  profiles.numeric.slice(0, 2).forEach((column) => {
    const histogram = createHistogramChart(rows, column);
    if (histogram) {
      charts.push(histogram);
    }
  });

  if (profiles.time.length && profiles.numeric.length) {
    const lineChart = createLineChart(rows, profiles.time[0], profiles.numeric[0]);
    if (lineChart) {
      charts.push(lineChart);
    }
  }

  if (profiles.categorical.length && profiles.numeric.length) {
    const barChart = createBarChart(rows, profiles.categorical[0], profiles.numeric[0]);
    if (barChart) {
      charts.push(barChart);
    }
  }

  if (profiles.numeric.length >= 2) {
    const scatter = createScatterChart(
      rows,
      profiles.numeric[0],
      profiles.numeric[1],
      profiles.categorical[0]
    );
    if (scatter) {
      charts.push(scatter);
    }
  }

  return charts;
};

const buildDatasetInsights = (rows, profiles) => {
  const insights = [];
  const rowCount = rows.length.toLocaleString();
  const columnCount = profiles.allColumns.length;
  insights.push(`Detected ${rowCount} rows across ${columnCount} columns.`);

  if (profiles.numeric.length) {
    const column = profiles.numeric[0];
    const values = rows
      .map((row) => parseNumericValue(row[column]))
      .filter((value) => Number.isFinite(value));
    if (values.length) {
      const average = values.reduce((sum, value) => sum + value, 0) / values.length;
      insights.push(`${column} averages ${average.toFixed(2)} based on the uploaded file.`);
    }
  }

  if (profiles.categorical.length) {
    const column = profiles.categorical[0];
    const frequency = rows.reduce((acc, row) => {
      const key = row[column] || 'Unknown';
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});
    const sorted = Object.entries(frequency).sort((a, b) => b[1] - a[1]);
    if (sorted.length) {
      const [topValue, count] = sorted[0];
      insights.push(`${topValue} appears ${count.toLocaleString()} times in ${column}.`);
    }
  }

  return insights.slice(0, MAX_DATASET_INSIGHTS);
};

const buildMetadataSummary = (rows, profiles, chartCount) => ({
  total_charts: chartCount,
  dataset_rows: rows.length,
  dataset_columns: profiles.allColumns.length,
  insights_generated: true,
});

const buildQualityIndicators = (rows, profiles) => {
  const totalCells = rows.length * Math.max(profiles.allColumns.length, 1);
  let emptyCells = 0;
  rows.forEach((row) => {
    profiles.allColumns.forEach((column) => {
      if (row[column] === undefined || row[column] === null || row[column] === '') {
        emptyCells += 1;
      }
    });
  });

  const completenessScore = totalCells ? Math.round(((totalCells - emptyCells) / totalCells) * 100) : 0;
  const structureScore = Math.round(
    ((profiles.numeric.length + profiles.time.length * 0.8) / Math.max(profiles.allColumns.length, 1)) * 100
  );
  const overallScore = Math.max(45, Math.min(95, Math.round((completenessScore + structureScore) / 2)));

  let rating = 'fair';
  if (overallScore >= 85) {
    rating = 'excellent';
  } else if (overallScore >= 70) {
    rating = 'good';
  } else if (overallScore < 55) {
    rating = 'poor';
  }

  return {
    overall_score: overallScore,
    rating,
  };
};

const Dashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [charts, setCharts] = useState([]);
  const [datasetName, setDatasetName] = useState('Dataset');
  const [summary, setSummary] = useState(null);
  const [qualityIndicators, setQualityIndicators] = useState(null);
  const [metadataSummary, setMetadataSummary] = useState(null);
  const [layout, setLayout] = useState(null);
  const [fullscreenChart, setFullscreenChart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [csvError, setCsvError] = useState('');
  const fileInputRef = useRef(null);

  const buildDashboardFromCsv = async (file) => {
    setCsvError('');
    setLoading(true);
    try {
      const text = await file.text();
      const { headers, rows } = parseCsvText(text);
      const profiles = inferColumnProfiles(rows, headers);
      const generatedCharts = generateChartsFromCsv(rows, profiles);

      if (!generatedCharts.length) {
        throw new Error('Unable to generate charts from this CSV. Please ensure it has numeric and categorical columns.');
      }

      const insights = buildDatasetInsights(rows, profiles);
      const metadataSummary = buildMetadataSummary(rows, profiles, generatedCharts.length);
      const quality = buildQualityIndicators(rows, profiles);

      setDatasetName(file.name.replace(/\.[^.]+$/, '') || 'Uploaded Dataset');
      setSummary({ dataset_insights: insights });
      setMetadataSummary(metadataSummary);
      setQualityIndicators(quality);
      setCharts(generatedCharts);
      setLayout(null);
    } catch (error) {
      console.error('Failed to create dashboard from CSV:', error);
      setCsvError(error.message || 'Unable to process this CSV file.');
      setCharts([]);
      setSummary(null);
      setMetadataSummary(null);
      setQualityIndicators(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLocalCsvUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    await buildDashboardFromCsv(file);
    // Reset input so the same file can be selected again
    // eslint-disable-next-line no-param-reassign
    event.target.value = '';
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        navigate('/login', { replace: true });
        return;
      }

      if (!sessionManager.isSessionValid()) {
        sessionManager.clearSession();
        try {
          await signOut(auth);
        } catch (error) {
          console.error('Error signing out expired session:', error);
        }
        navigate('/login', { replace: true });
        return;
      }
      
      setIsCheckingSession(false);
    });

    return () => unsubscribe();
  }, [navigate]);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setCsvError('');
      
      // First check if data was passed via navigation state
      let dashboardData = location.state?.dashboardData;

      // If no state, try to fetch from MongoDB using session ID
      if (!dashboardData) {
        const sessionId = localStorage.getItem('sessionId') || localStorage.getItem('chatSessionId');
        if (sessionId) {
          try {
            const response = await apiGet(`/chat/sessions/${sessionId}/dashboard`);
            if (response.ok) {
              dashboardData = await response.json();
            }
          } catch (error) {
            console.error('Failed to fetch dashboard data from MongoDB:', error);
          }
        }
      }

      if (dashboardData) {
        setCharts(dashboardData.charts || []);
        setDatasetName(dashboardData.dataset_name || 'Dataset');
        setSummary(dashboardData.summary || null);
        setQualityIndicators(dashboardData.quality_indicators || null);
        setMetadataSummary(dashboardData.metadata_summary || null);
        setLayout(dashboardData.layout || null);
      } else {
        setCharts([]);
        setSummary(null);
        setQualityIndicators(null);
        setMetadataSummary(null);
        setLayout(null);
      }

      setLoading(false);
    };
    
    loadDashboard();
  }, [location.state]);

  const orderedCharts = useMemo(() => {
    if (!layout?.sections || !charts.length) {
      return charts;
    }

    const layoutOrder = layout.sections
      .filter((section) => section.type === 'grid')
      .flatMap((section) => (Array.isArray(section.items) ? section.items : []))
      .map((item) => item?.id)
      .filter(Boolean);

    if (!layoutOrder.length) {
      return charts;
    }

    const chartById = new Map(charts.filter((chart) => chart.id).map((chart) => [chart.id, chart]));
    const ordered = layoutOrder
      .map((id) => chartById.get(id))
      .filter(Boolean);
    const remaining = charts.filter((chart) => !chart.id || !layoutOrder.includes(chart.id));
    return [...ordered, ...remaining];
  }, [charts, layout]);

  const chartKeyMap = useMemo(() => {
    const map = new Map();
    orderedCharts.forEach((chart, index) => {
      const key = chart.id || `${chart.type || 'chart'}-${index}`;
      map.set(chart, key);
    });
    return map;
  }, [orderedCharts]);

  const kpiCharts = useMemo(
    () => orderedCharts.filter((chart) => chart.type?.toLowerCase() === 'kpi'),
    [orderedCharts]
  );

  const visualCharts = useMemo(
    () => orderedCharts.filter((chart) => chart.type?.toLowerCase() !== 'kpi'),
    [orderedCharts]
  );

  const primaryCharts = useMemo(() => {
    if (!visualCharts.length) {
      return [];
    }

    const prioritizedTypeGroups = [
      ['correlation_heatmap', 'heatmap'],
      ['time_series', 'line'],
      ['scatter', 'scatter_plot'],
      ['bar', 'grouped_bar'],
      ['histogram'],
      ['treemap'],
      ['funnel'],
      ['sankey'],
      ['stacked_area'],
      ['box_plot', 'box'],
      ['pie'],
    ];

    const selected = [];
    const used = new Set();

    const registerChart = (chart) => {
      if (!chart || selected.length >= PRIMARY_CHART_LIMIT) {
        return;
      }
      const key = chartKeyMap.get(chart);
      if (!key || used.has(key)) {
        return;
      }
      used.add(key);
      selected.push(chart);
    };

    prioritizedTypeGroups.forEach((group) => {
      if (selected.length >= PRIMARY_CHART_LIMIT) {
        return;
      }
      const chart = visualCharts.find((item) => group.includes(item.type?.toLowerCase?.() ?? ''));
      registerChart(chart);
    });

    for (const chart of visualCharts) {
      if (selected.length >= PRIMARY_CHART_LIMIT) {
        break;
      }
      registerChart(chart);
    }

    return selected;
  }, [visualCharts, chartKeyMap]);

  const hiddenChartCount = Math.max(visualCharts.length - primaryCharts.length, 0);

  const summaryCards = useMemo(() => {
    const cards = [];

    if (metadataSummary) {
      if (metadataSummary.total_charts !== undefined) {
        cards.push({ label: 'Visualizations', value: formatInteger(metadataSummary.total_charts) });
      }
      if (metadataSummary.dataset_rows !== undefined) {
        cards.push({ label: 'Rows Analysed', value: formatInteger(metadataSummary.dataset_rows) });
      }
      if (metadataSummary.dataset_columns !== undefined) {
        cards.push({ label: 'Columns', value: formatInteger(metadataSummary.dataset_columns) });
      }
      if (metadataSummary.insights_generated !== undefined) {
        cards.push({ label: 'AI Insights', value: metadataSummary.insights_generated ? 'Enabled' : 'Disabled' });
      }
    }

    if (qualityIndicators?.overall_score !== undefined) {
      cards.push({
        label: 'Data Quality',
        value: `${formatInteger(qualityIndicators.overall_score)}%`,
        badge: capitalize(qualityIndicators.rating),
        badgeKey: qualityIndicators.rating,
      });
    }

    return cards;
  }, [metadataSummary, qualityIndicators]);

  const datasetInsights = useMemo(
    () => {
      if (!Array.isArray(summary?.dataset_insights)) {
        return [];
      }
      return summary.dataset_insights.filter(Boolean).slice(0, MAX_DATASET_INSIGHTS);
    },
    [summary]
  );

  const renderCsvError = () => (
    <div className="rounded-xl border border-rose-500/50 bg-rose-500/10 px-4 py-3 text-left text-xs text-rose-200">
      {csvError}
    </div>
  );

  const renderChart = (chart, key, options = {}) => {
    const { fullscreen = false } = options;
    const rawType = chart.type?.toLowerCase?.() ?? 'unknown';
    const type = rawType === 'box' ? 'box_plot' : rawType;
    const registryEntry = chartRegistry[type] || chartRegistry.default;
    const Component = registryEntry.component;
    const chartKey = chart.id || `${type}-${key}`;
    const displayTitle = chart.title || capitalize(type.replace(/_/g, ' '));

    if (registryEntry.mode === 'kpi') {
      return <Component key={chartKey} chart={chart} />;
    }

    if (registryEntry.mode === 'figure') {
      return (
        <Component
          key={chartKey}
          figure={chart.figure || {}}
          title={displayTitle}
          onFullscreen={fullscreen ? undefined : () => setFullscreenChart(chart)}
        />
      );
    }

    return (
      <Component
        key={chartKey}
        data={chart.figure?.data || []}
        layout={chart.figure?.layout || {}}
        title={displayTitle}
        onFullscreen={fullscreen ? undefined : () => setFullscreenChart(chart)}
      />
    );
  };

  // Show loading state while checking session
  if (isCheckingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0d1117]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-white border-r-transparent"></div>
          <p className="mt-4 text-sm text-slate-400">Checking session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-screen flex-col bg-[#0d1117] text-slate-100">
      <header className="sticky top-0 z-30 border-b border-slate-800/60 bg-[#0d1117]/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/chat')}
              type="button"
              className="flex items-center gap-2 rounded-xl border border-slate-800/80 bg-slate-900/80 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:border-slate-700 hover:text-white"
            >
              <FiArrowLeft className="text-sm" />
              Back to Chat
            </button>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600">
                <HiSparkles className="text-xl text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-white">{datasetName}</h1>
                <p className="text-xs text-slate-400">{charts.length} visualizations generated</p>
              </div>
            </div>
          </div>

          {qualityIndicators?.rating ? (
            <span
              className={`rounded-full px-4 py-1 text-xs font-medium uppercase tracking-wide ${ratingStyles[qualityIndicators.rating] || 'border border-slate-700 bg-slate-800 text-slate-200'
                }`}
            >
              Data Quality: {capitalize(qualityIndicators.rating)}
            </span>
          ) : null}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <input
          type="file"
          accept=".csv,text/csv"
          ref={fileInputRef}
          className="hidden"
          onChange={handleLocalCsvUpload}
        />
        <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-8 px-6 pb-12 pt-6">
          {loading ? (
            <div className="flex h-[60vh] items-center justify-center text-sm text-slate-400">
              Preparing your dashboard…
            </div>
          ) : charts.length === 0 ? (
            <div className="flex h-[60vh] flex-col items-center justify-center text-center">
              <HiSparkles className="mb-4 text-5xl text-slate-600" />
              <h2 className="text-xl font-semibold text-white">No visualizations yet</h2>
              <p className="mt-2 max-w-md text-sm text-slate-400">
                Upload a dataset from the chat experience or use a CSV file to generate an interactive dashboard automatically.
              </p>
              <div className="mt-6 flex flex-col gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                  className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:border-slate-500"
                >
                  Build dashboard from CSV
                </button>
                <button
                  onClick={() => navigate('/chat')}
                  type="button"
                  className="rounded-xl bg-white px-5 py-2 text-sm font-medium text-[#0d1117] transition hover:bg-slate-200"
                >
                  Upload via conversational flow
                </button>
                {csvError ? renderCsvError() : null}
                <p className="text-xs text-slate-500">Accepted format: .csv up to 5MB.</p>
              </div>
            </div>
          ) : (
            <>
              {summaryCards.length > 0 && (
                <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
                  {summaryCards.map((card) => (
                    <div
                      key={card.label}
                      className="group rounded-2xl border border-slate-800/60 bg-gradient-to-br from-slate-900/80 to-slate-900/40 p-5 shadow-lg shadow-black/20 transition-all hover:border-slate-700/80 hover:shadow-xl hover:shadow-black/30"
                    >
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500/90">
                        {card.label}
                      </p>
                      <p className="mt-4 text-3xl font-bold text-white">{card.value}</p>
                      {card.badge ? (
                        <span
                          className={`mt-5 inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide ${ratingStyles[card.badgeKey] || 'border border-slate-700 bg-slate-800 text-slate-200'
                            }`}
                        >
                          <HiSparkles className="text-xs" />
                          {card.badge}
                        </span>
                      ) : null}
                    </div>
                  ))}
                </section>
              )}

              {datasetInsights.length > 0 && (
                <section className="rounded-2xl border border-sky-900/30 bg-gradient-to-br from-slate-900/80 to-sky-950/20 p-6 shadow-lg shadow-black/30 backdrop-blur-sm">
                  <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-sky-300">
                    <HiSparkles className="text-lg text-sky-400" /> Key Insights
                  </h2>
                  <ul className="mt-5 space-y-4 text-sm text-slate-200">
                    {datasetInsights.map((insight, index) => (
                      <li key={`insight-${index}`} className="flex gap-3 leading-relaxed">
                        <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 shadow-sm shadow-sky-500/50" />
                        <span className="text-slate-300">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {kpiCharts.length > 0 && (
                <section className="grid gap-4 auto-rows-[minmax(140px,1fr)] grid-cols-1 sm:grid-cols-2">
                  {kpiCharts.slice(0, MAX_KPI_CARDS).map((chart, index) => renderChart(chart, `kpi-${index}`))}
                </section>
              )}

              <section className="grid gap-6 auto-rows-[minmax(320px,1fr)] grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
                {primaryCharts.map((chart, index) => renderChart(chart, `chart-${index}`))}
              </section>

              {hiddenChartCount > 0 && (
                <p className="text-center text-xs text-slate-500">
                  {hiddenChartCount} additional visualizations were generated and hidden to keep this dashboard succinct.
                </p>
              )}
            </>
          )}
        </div>
      </main>

      {fullscreenChart && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 px-6 py-8"
          onClick={() => setFullscreenChart(null)}
        >
          <div
            className="flex h-full w-full max-w-[1600px] flex-col overflow-hidden rounded-3xl border border-slate-800/70 bg-slate-900/90 p-4 shadow-2xl shadow-black/60"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-slate-400/80">Fullscreen View</p>
                <h2 className="text-xl font-semibold text-white">{fullscreenChart.title}</h2>
              </div>
              <button
                onClick={() => setFullscreenChart(null)}
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-700/70 text-slate-300 transition hover:border-slate-500 hover:text-white"
              >
                <FiX className="text-lg" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/80 p-3">
              {renderChart(fullscreenChart, 'fullscreen', { fullscreen: true })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
