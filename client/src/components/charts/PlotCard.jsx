import { useMemo, useRef } from 'react';
import Plot from '../Plot';
import DashboardTile from '../DashboardTile';

const PlotCard = ({ figure, title, onFullscreen }) => {
  const plotRef = useRef(null);
  const data = figure?.data ?? [];
  const baseLayout = figure?.layout ?? {};

  const mergedLayout = useMemo(() => ({
    ...baseLayout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: baseLayout.plot_bgcolor ?? 'rgba(13,17,23,0.85)',
    font: {
      color: '#e5e7eb',
      family: 'Inter, system-ui, sans-serif',
      ...baseLayout.font,
    },
    margin: {
      l: 56,
      r: 32,
      t: 56,
      b: 56,
      ...baseLayout.margin,
    },
    xaxis: {
      color: '#9ca3af',
      gridcolor: '#1f2a37',
      ...baseLayout.xaxis,
    },
    yaxis: {
      color: '#9ca3af',
      gridcolor: '#1f2a37',
      ...baseLayout.yaxis,
    },
  }), [baseLayout]);

  const handleDownload = () => {
    const filename = (title || 'chart').replace(/\s+/g, '_').toLowerCase();
    if (plotRef.current?.downloadImage) {
      plotRef.current
        .downloadImage({ format: 'png', filename, height: 720, width: 1280, scale: 2 })
        .catch(() => {});
    }
  };

  return (
    <DashboardTile title={title} onFullscreen={onFullscreen} onDownload={handleDownload}>
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

export default PlotCard;
