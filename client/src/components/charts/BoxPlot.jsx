import { useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import DashboardTile from '../DashboardTile';

const BoxPlot = ({ data, layout, title, onFullscreen }) => {
  const plotRef = useRef(null);

  const mergedLayout = useMemo(() => ({
    ...layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(13,17,23,0.85)',
    font: {
      color: '#e5e7eb',
      family: 'Inter, system-ui, sans-serif',
    },
    xaxis: {
      gridcolor: '#1f2a37',
      color: '#9ca3af',
      ...layout?.xaxis,
    },
    yaxis: {
      gridcolor: '#1f2a37',
      color: '#9ca3af',
      ...layout?.yaxis,
    },
    margin: { l: 56, r: 24, t: 48, b: 60, ...layout?.margin },
  }), [layout]);

  const handleDownload = () => {
    const filename = (title || 'box_plot').replace(/\s+/g, '_').toLowerCase();
    if (plotRef.current?.downloadImage) {
      plotRef.current.downloadImage({
        format: 'png',
        filename,
        height: 720,
        width: 1280,
        scale: 2,
      }).catch(() => {});
    }
  };

  return (
    <DashboardTile
      title={title || 'Box Plot'}
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

export default BoxPlot;
