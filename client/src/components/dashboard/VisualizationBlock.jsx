import { useState } from 'react';
import { HiChartBar, HiChartPie, HiSparkles } from 'react-icons/hi2';
import { FiRefreshCw, FiMaximize2, FiMinimize2, FiGrid } from 'react-icons/fi';
import Plot from '../Plot';

const getBlockIcon = (type) => {
  const icons = {
    chart: HiChartBar,
    pie: HiChartPie,
    table: FiGrid,
    metric: HiSparkles,
  };
  return icons[type] || HiChartBar;
};

const MetricDisplay = ({ data }) => {
  if (!data || !data.metrics) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
      {data.metrics.map((metric, index) => (
        <div
          key={index}
          className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50"
        >
          <div className="text-slate-400 text-sm mb-1">{metric.label}</div>
          <div className="text-2xl font-bold text-slate-100">
            {typeof metric.value === 'number'
              ? metric.value.toLocaleString()
              : metric.value}
          </div>
          {metric.change && (
            <div
              className={`text-sm mt-1 ${
                metric.change > 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {metric.change > 0 ? '↑' : '↓'} {Math.abs(metric.change)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const TableDisplay = ({ data }) => {
  if (!data || !data.rows || data.rows.length === 0) {
    return <div className="p-6 text-slate-400">No data available</div>;
  }

  const columns = Object.keys(data.rows[0]);

  return (
    <div className="overflow-x-auto p-4">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-700">
            {columns.map((col) => (
              <th key={col} className="px-4 py-3 text-slate-300 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.slice(0, 10).map((row, index) => (
            <tr key={index} className="border-b border-slate-800 hover:bg-slate-800/30">
              {columns.map((col) => (
                <td key={col} className="px-4 py-3 text-slate-400">
                  {row[col]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.rows.length > 10 && (
        <div className="text-center py-3 text-slate-500 text-sm">
          Showing 10 of {data.rows.length} rows
        </div>
      )}
    </div>
  );
};

const ChartDisplay = ({ data }) => {
  if (!data || !data.figure) {
    return <div className="p-6 text-slate-400">No chart data available</div>;
  }

  return (
    <div className="w-full h-[350px] p-4">
      <Plot
        data={data.figure.data}
        layout={{
          ...data.figure.layout,
          autosize: true,
          height: 300,
          margin: { t: 40, r: 20, b: 60, l: 60 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#e2e8f0' },
          xaxis: {
            ...data.figure.layout?.xaxis,
            gridcolor: '#334155',
            color: '#cbd5e1',
          },
          yaxis: {
            ...data.figure.layout?.yaxis,
            gridcolor: '#334155',
            color: '#cbd5e1',
          },
        }}
        config={{
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          responsive: true,
        }}
        className="w-full h-full"
        useResizeHandler={true}
      />
    </div>
  );
};

const VisualizationBlock = ({ block, isExpanded, onExpand, onRefresh }) => {
  const [isLoading, setIsLoading] = useState(false);
  const Icon = getBlockIcon(block.visualizationType);

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      await onRefresh?.();
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      );
    }

    switch (block.visualizationType) {
      case 'metric':
        return <MetricDisplay data={block.data} />;
      case 'table':
        return <TableDisplay data={block.data} />;
      case 'chart':
      case 'pie':
      default:
        return <ChartDisplay data={block.data} />;
    }
  };

  return (
    <div
      className={`rounded-lg border border-slate-700/50 bg-slate-800/30 backdrop-blur-sm transition-all duration-300 ${
        isExpanded ? 'col-span-full row-span-2' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-200 font-medium">{block.title}</h3>
            {block.description && (
              <p className="text-slate-500 text-sm mt-0.5">{block.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-2 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
              title="Refresh data"
            >
              <FiRefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
          <button
            onClick={onExpand}
            className="p-2 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors"
            title={isExpanded ? 'Minimize' : 'Expand'}
          >
            {isExpanded ? (
              <FiMinimize2 className="w-4 h-4" />
            ) : (
              <FiMaximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className={isExpanded ? 'h-[600px]' : 'h-auto'}>{renderContent()}</div>

      {/* Footer with metadata */}
      {block.metadata && (
        <div className="px-4 py-2 border-t border-slate-700/50 text-xs text-slate-500">
          {block.metadata.lastUpdated && (
            <span>Last updated: {new Date(block.metadata.lastUpdated).toLocaleString()}</span>
          )}
        </div>
      )}
    </div>
  );
};

export default VisualizationBlock;
