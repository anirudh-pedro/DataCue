/**
 * InsightsPanel - Display key insights from data analysis
 * 
 * Features:
 * - Horizontal scrolling list of insights
 * - Icon-based visual indicators
 * - Compact display for dashboard integration
 */

import { HiLightBulb, HiSparkles, HiArrowTrendingUp } from 'react-icons/hi2';

const InsightsPanel = ({ insights }) => {
  if (!insights || !Array.isArray(insights) || insights.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        No insights available
      </div>
    );
  }

  return (
    <div className="h-full flex items-center gap-4 overflow-x-auto px-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
      {insights.map((insight, index) => (
        <InsightCard key={index} insight={insight} index={index} />
      ))}
    </div>
  );
};

const InsightCard = ({ insight, index }) => {
  // Get icon based on index (cycle through)
  const icons = [HiLightBulb, HiSparkles, HiArrowTrendingUp];
  const Icon = icons[index % icons.length];
  
  // Get color based on index
  const colors = [
    { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
    { bg: 'bg-indigo-500/20', text: 'text-indigo-400', border: 'border-indigo-500/30' },
    { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  ];
  const color = colors[index % colors.length];

  // Handle both string and object insights
  const text = typeof insight === 'string' ? insight : insight.text || insight.message || JSON.stringify(insight);

  return (
    <div className={`
      flex-shrink-0 flex items-center gap-3
      px-4 py-2 rounded-lg
      border ${color.border} ${color.bg}
      max-w-[400px]
    `}>
      <Icon className={`${color.text} text-lg flex-shrink-0`} />
      <p className="text-sm text-slate-300 line-clamp-2">
        {text}
      </p>
    </div>
  );
};

export default InsightsPanel;
