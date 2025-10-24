import { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { HiSparkles } from 'react-icons/hi2';
import { FiDownload, FiMaximize2 } from 'react-icons/fi';

const ChartMessage = ({ chart, timestamp, messageId }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [plotlyData, setPlotlyData] = useState(null);
  const [plotlyLayout, setPlotlyLayout] = useState(null);
  const chartDomId = useMemo(() => {
    if (messageId) {
      return `chart-${messageId}`;
    }
    if (chart?.chart_id) {
      return `chart-${chart.chart_id}`;
    }
    const fallback = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2, 10);
    return `chart-${fallback}`;
  }, [messageId, chart?.chart_id]);

  useEffect(() => {
    if (!chart?.figure) return;

    try {
      const figure = chart.figure;
      setPlotlyData(figure.data || []);
      setPlotlyLayout({
        ...(figure.layout || {}),
        autosize: true,
        margin: { l: 50, r: 30, t: 50, b: 50 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#fff' },
        xaxis: { ...figure.layout?.xaxis, gridcolor: '#374151' },
        yaxis: { ...figure.layout?.yaxis, gridcolor: '#374151' },
      });
    } catch (error) {
      console.error('Error parsing chart figure:', error);
    }
  }, [chart]);

  const handleDownload = () => {
    const graphDiv = document.getElementById(chartDomId);
    const plotly = window?.Plotly;

    if (!graphDiv || !plotly?.downloadImage) {
      console.warn('Unable to download chart — Plotly instance not available.');
      return;
    }

    const filenameBase = chart?.title ? chart.title.replace(/[^a-z0-9-_]+/gi, '_') : 'datacue_chart';

    plotly
      .downloadImage(graphDiv, {
        format: 'png',
        filename: filenameBase.toLowerCase() || 'datacue_chart',
      })
      .catch((error) => {
        console.error('Failed to download chart image:', error);
      });
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!plotlyData || !plotlyLayout) {
    return (
      <div className="flex items-start space-x-3 group animate-fadeIn">
        <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
          <HiSparkles className="text-white text-lg" />
        </div>
        <div className="flex-1 max-w-[80%]">
          <div className="rounded-2xl rounded-tl-none bg-gray-900 border border-gray-800 p-4">
            <p className="text-gray-400 text-sm">Loading chart...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-start space-x-3 group animate-fadeIn">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
          <HiSparkles className="text-white text-lg" />
        </div>

        {/* Chart Content */}
        <div className="flex-1 max-w-[85%]">
          <div className="rounded-2xl rounded-tl-none bg-gray-900 border border-gray-800 p-4 relative">
            {/* Chart Title */}
            {chart.title && (
              <h3 className="text-white text-sm font-semibold mb-3">{chart.title}</h3>
            )}

            {/* Action Buttons */}
            <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
              <button
                onClick={toggleFullscreen}
                className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                title="Expand chart"
              >
                <FiMaximize2 className="text-gray-400 text-sm" />
              </button>
              <button
                onClick={handleDownload}
                className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                title="Download chart"
              >
                <FiDownload className="text-gray-400 text-sm" />
              </button>
            </div>

            {/* Plotly Chart */}
            <div className="bg-gray-950 rounded-lg p-2 overflow-hidden">
              <Plot
                data={plotlyData}
                layout={plotlyLayout}
                config={{
                  responsive: true,
                  displayModeBar: false,
                  displaylogo: false,
                }}
                style={{ width: '100%', height: '400px' }}
                useResizeHandler={true}
                divId={chartDomId}
              />
            </div>

            {/* Chart Insights */}
            {chart.insights && typeof chart.insights === 'object' && (
              <div className="mt-3 pt-3 border-t border-gray-800">
                <p className="text-xs text-gray-400 mb-2">Key Insights:</p>
                <div className="text-xs text-gray-300 space-y-1">
                  {Object.entries(chart.insights).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-500">{key.replace(/_/g, ' ')}:</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          {timestamp && (
            <p className="text-xs text-gray-500 mt-1 px-2">{timestamp}</p>
          )}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8"
          onClick={toggleFullscreen}
        >
          <div
            className="w-full h-full max-w-7xl max-h-full bg-gray-900 rounded-2xl p-6 overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white text-lg font-semibold">{chart.title}</h2>
              <button
                onClick={toggleFullscreen}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <div className="bg-gray-950 rounded-lg p-4">
              <Plot
                data={plotlyData}
                layout={{ ...plotlyLayout, height: 600 }}
                config={{
                  responsive: true,
                  displayModeBar: true,
                  displaylogo: false,
                }}
                style={{ width: '100%', height: '600px' }}
                useResizeHandler={true}
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChartMessage;
