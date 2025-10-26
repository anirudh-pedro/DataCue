import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { onAuthStateChanged } from 'firebase/auth';
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

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      const otpVerified = sessionStorage.getItem('otpVerified') === 'true';

      if (!user) {
        navigate('/login', { replace: true });
        return;
      }

      if (!otpVerified) {
        if (user.email) {
          sessionStorage.setItem('otpEmail', user.email);
        }
        navigate('/verify-otp', { replace: true, state: { email: user.email } });
      }
    });

    return () => unsubscribe();
  }, [navigate]);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      
      // First check if data was passed via navigation state
      let dashboardData = location.state?.dashboardData;

      // If no state, try to fetch from MongoDB using session ID
      if (!dashboardData) {
        const sessionId = localStorage.getItem('sessionId') || localStorage.getItem('chatSessionId');
        if (sessionId) {
          try {
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
            const response = await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions/${sessionId}/dashboard`);
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
                Upload a dataset from the chat experience to generate an interactive dashboard automatically.
              </p>
              <button
                onClick={() => navigate('/chat')}
                type="button"
                className="mt-6 rounded-xl bg-white px-5 py-2 text-sm font-medium text-[#0d1117] transition hover:bg-slate-200"
              >
                Upload a dataset
              </button>
            </div>
          ) : (
            <>
              {summaryCards.length > 0 && (
                <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {summaryCards.map((card) => (
                    <div
                      key={card.label}
                      className="rounded-2xl border border-slate-800/60 bg-slate-900/60 p-4 shadow-lg shadow-black/10"
                    >
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400/90">
                        {card.label}
                      </p>
                      <p className="mt-3 text-2xl font-semibold text-white">{card.value}</p>
                      {card.badge ? (
                        <span
                          className={`mt-4 inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-semibold ${ratingStyles[card.badgeKey] || 'border border-slate-700 bg-slate-800 text-slate-200'
                            }`}
                        >
                          <HiSparkles className="text-sm" />
                          {card.badge}
                        </span>
                      ) : null}
                    </div>
                  ))}
                </section>
              )}

              {datasetInsights.length > 0 && (
                <section className="rounded-2xl border border-slate-800/60 bg-slate-900/60 p-6 shadow-inner shadow-black/20">
                  <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
                    <HiSparkles className="text-base text-sky-400" /> AI Highlights
                  </h2>
                  <ul className="mt-4 space-y-3 text-sm text-slate-300">
                    {datasetInsights.map((insight, index) => (
                      <li key={`insight-${index}`} className="flex gap-3">
                        <span className="mt-2 h-1.5 w-1.5 rounded-full bg-sky-500" />
                        <span>{insight}</span>
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

              <section className="grid gap-6 auto-rows-[minmax(280px,1fr)] grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
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
