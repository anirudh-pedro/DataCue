import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import BarChart from '../components/charts/BarChart';
import LineChart from '../components/charts/LineChart';
import ScatterPlot from '../components/charts/ScatterPlot';
import Histogram from '../components/charts/Histogram';
import PieChart from '../components/charts/PieChart';
import Heatmap from '../components/charts/Heatmap';
import BoxPlot from '../components/charts/BoxPlot';
import { HiSparkles } from 'react-icons/hi2';
import { FiArrowLeft } from 'react-icons/fi';

const Dashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [charts, setCharts] = useState([]);
  const [datasetName, setDatasetName] = useState('Dataset');
  const [summary, setSummary] = useState(null);
  const [fullscreenChart, setFullscreenChart] = useState(null);

  useEffect(() => {
    // Get charts from navigation state or sessionStorage
    let dashboardData = location.state?.dashboardData;
    
    // Fallback to sessionStorage if state is missing
    if (!dashboardData) {
      const stored = sessionStorage.getItem('dashboardData');
      if (stored) {
        try {
          dashboardData = JSON.parse(stored);
        } catch (e) {
          console.error('Failed to parse stored dashboard data:', e);
        }
      }
    }
    
    if (dashboardData) {
      setCharts(dashboardData.charts || []);
      setDatasetName(dashboardData.dataset_name || 'Dataset');
      setSummary(dashboardData.summary);
    }
  }, [location.state]);

  const renderChart = (chart, index) => {
    const chartProps = {
      data: chart.figure?.data || [],
      layout: chart.figure?.layout || {},
      title: chart.title,
      onFullscreen: () => setFullscreenChart(chart),
    };

    const chartType = chart.type?.toLowerCase();

    switch (chartType) {
      case 'bar':
      case 'grouped_bar':
        return <BarChart key={index} {...chartProps} />;
      
      case 'time_series':
      case 'line':
        return <LineChart key={index} {...chartProps} />;
      
      case 'scatter':
      case 'scatter_plot':
        return <ScatterPlot key={index} {...chartProps} />;
      
      case 'histogram':
        return <Histogram key={index} {...chartProps} />;
      
      case 'pie':
        return <PieChart key={index} {...chartProps} />;
      
      case 'heatmap':
      case 'correlation_heatmap':
        return <Heatmap key={index} {...chartProps} />;
      
      case 'box':
      case 'box_plot':
        return <BoxPlot key={index} {...chartProps} />;
      
      default:
        // Default to bar chart for unknown types
        return <BarChart key={index} {...chartProps} />;
    }
  };

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/chat')}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              title="Back to Chat"
            >
              <FiArrowLeft className="text-gray-400 text-lg" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <HiSparkles className="text-white text-xl" />
              </div>
              <div>
                <h1 className="text-white text-lg font-semibold">{datasetName}</h1>
                <p className="text-gray-400 text-xs">
                  {charts.length} visualizations generated
                </p>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          {summary && (
            <div className="flex gap-6">
              {summary.dataset_size && (
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Dataset Size</p>
                  <p className="text-white text-sm font-semibold">{summary.dataset_size}</p>
                </div>
              )}
              {summary.quality_score && (
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Quality Score</p>
                  <p className="text-white text-sm font-semibold">{summary.quality_score}</p>
                </div>
              )}
              {summary.strong_correlations !== undefined && (
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Strong Correlations</p>
                  <p className="text-white text-sm font-semibold">{summary.strong_correlations}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Dashboard Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {charts.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <HiSparkles className="text-gray-600 text-6xl mx-auto mb-4" />
                <h2 className="text-white text-xl font-semibold mb-2">No Visualizations Yet</h2>
                <p className="text-gray-400 text-sm">
                  Upload a dataset to generate automatic dashboards
                </p>
                <button
                  onClick={() => navigate('/chat')}
                  className="mt-4 px-6 py-2 bg-white text-black rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Go to Chat
                </button>
              </div>
            </div>
          ) : (
            <div 
              className="grid gap-6 h-full"
              style={{
                gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
                gridAutoRows: 'minmax(350px, 1fr)',
              }}
            >
              {charts.map((chart, index) => renderChart(chart, index))}
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {fullscreenChart && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-8"
          onClick={() => setFullscreenChart(null)}
        >
          <div
            className="w-full h-full max-w-7xl max-h-full bg-gray-900 rounded-2xl p-6 overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white text-xl font-semibold">{fullscreenChart.title}</h2>
              <button
                onClick={() => setFullscreenChart(null)}
                className="text-gray-400 hover:text-white text-3xl leading-none"
              >
                ×
              </button>
            </div>
            <div className="flex-1 bg-gray-950 rounded-xl p-4">
              {renderChart({ ...fullscreenChart, onFullscreen: () => {} }, 'fullscreen')}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
