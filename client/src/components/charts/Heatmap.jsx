import Plot from 'react-plotly.js';
import { FiMaximize2, FiDownload } from 'react-icons/fi';

const Heatmap = ({ data, layout, title, onFullscreen }) => {
  const defaultLayout = {
    ...layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(17, 24, 39, 0.5)',
    font: { color: '#e5e7eb', family: 'Inter, system-ui, sans-serif' },
    xaxis: {
      ...layout?.xaxis,
      color: '#9ca3af',
      side: 'bottom',
    },
    yaxis: {
      ...layout?.yaxis,
      color: '#9ca3af',
      autorange: 'reversed',
    },
    margin: { l: 100, r: 100, t: 50, b: 100 },
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-white text-sm font-semibold">{title || 'Heatmap'}</h3>
        <div className="flex gap-2">
          <button
            onClick={onFullscreen}
            className="p-1.5 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <FiMaximize2 className="text-gray-400 text-sm" />
          </button>
          <button className="p-1.5 hover:bg-gray-800 rounded-lg transition-colors">
            <FiDownload className="text-gray-400 text-sm" />
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <Plot
          data={data}
          layout={defaultLayout}
          config={{ responsive: true, displayModeBar: false, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
};

export default Heatmap;
