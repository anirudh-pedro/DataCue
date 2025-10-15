import { useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import DashboardTile from '../DashboardTile';

const PieChart = ({ data, layout, title, onFullscreen }) => {
  const plotRef = useRef(null);

  const mergedLayout = useMemo(() => ({
    ...layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(13,17,23,0)',
    font: {
      color: '#e5e7eb',
      family: 'Inter, system-ui, sans-serif',
    },
    margin: { l: 24, r: 24, t: 48, b: 24, ...layout?.margin },
    showlegend: true,
    legend: {
      font: { color: '#9ca3af' },
      bgcolor: 'rgba(0,0,0,0)',
      ...layout?.legend,
    },
  }), [layout]);

  const handleDownload = () => {
    const filename = (title || 'pie_chart').replace(/\s+/g, '_').toLowerCase();
    if (plotRef.current?.downloadImage) {
      plotRef.current.downloadImage({
        format: 'png',
        filename,
        height: 720,
        width: 720,
        scale: 2,
      }).catch(() => {});
    }
  };

  return (
    <DashboardTile
      title={title || 'Pie Chart'}
      onFullscreen={onFullscreen}
      onDownload={handleDownload}
    >
      <Plot
        ref={plotRef}
        data={data}
        layout={mergedLayout}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['toImage'],
          scrollZoom: true,
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </DashboardTile>
  );
};

export default PieChart;
