import { useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import DashboardTile from '../DashboardTile';

const Heatmap = ({ data, layout, title, onFullscreen }) => {
  const plotRef = useRef(null);

  const mergedLayout = useMemo(() => ({
    ...layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(13,17,23,0.9)',
    font: {
      color: '#e5e7eb',
      family: 'Inter, system-ui, sans-serif',
    },
    xaxis: {
      side: 'bottom',
      color: '#94a3b8',
      tickfont: { color: '#cbd5f5' },
      ...layout?.xaxis,
    },
    yaxis: {
      autorange: 'reversed',
      color: '#94a3b8',
      tickfont: { color: '#cbd5f5' },
      ...layout?.yaxis,
    },
    margin: { l: 96, r: 48, t: 56, b: 96, ...layout?.margin },
    coloraxis: {
      ...layout?.coloraxis,
      colorbar: {
        outlinewidth: 0,
        tickcolor: '#94a3b8',
        title: layout?.coloraxis?.colorbar?.title ?? 'Correlation',
        ...layout?.coloraxis?.colorbar,
      },
    },
  }), [layout]);

  const handleDownload = () => {
    const filename = (title || 'heatmap').replace(/\s+/g, '_').toLowerCase();
    if (plotRef.current?.downloadImage) {
      plotRef.current.downloadImage({
        format: 'png',
        filename,
        height: 800,
        width: 1400,
        scale: 2,
      }).catch(() => {});
    }
  };

  return (
    <DashboardTile
      title={title || 'Heatmap'}
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

export default Heatmap;
