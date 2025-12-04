import { useState } from 'react';
import VisualizationBlock from './VisualizationBlock';

const DashboardGrid = ({ blocks, onRefreshBlock, isLoading }) => {
  const [expandedBlock, setExpandedBlock] = useState(null);

  const handleExpand = (blockId) => {
    setExpandedBlock(expandedBlock === blockId ? null : blockId);
  };

  if (isLoading) {
    return (
      <div className="grid gap-6 p-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-80 rounded-lg border border-slate-700/50 bg-slate-800/30 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (!blocks || blocks.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-slate-400 text-lg">No visualization blocks available</p>
          <p className="text-slate-500 text-sm mt-2">Upload data to generate insights</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6 p-6 auto-rows-auto">
      {blocks.map((block, index) => (
        <VisualizationBlock
          key={block.id || index}
          block={block}
          isExpanded={expandedBlock === block.id}
          onExpand={() => handleExpand(block.id)}
          onRefresh={() => onRefreshBlock?.(block.id)}
        />
      ))}
    </div>
  );
};

export default DashboardGrid;
