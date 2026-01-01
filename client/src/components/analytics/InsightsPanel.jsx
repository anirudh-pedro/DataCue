/**
 * InsightsPanel - Display key insights from data analysis (Dark Theme)
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
      <div className="h-full flex items-center justify-center text-gray-500 text-sm">
        No insights available
      </div>
    );
  }

  return (
    <div className="h-full flex items-center gap-3 overflow-x-auto px-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
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
  
  // Get color based on index (Power BI style colors - dark theme)
  const colors = [
    { bg: 'bg-amber-900/30', text: 'text-amber-400', border: 'border-amber-700/50' },
    { bg: 'bg-blue-900/30', text: 'text-blue-400', border: 'border-blue-700/50' },
    { bg: 'bg-emerald-900/30', text: 'text-emerald-400', border: 'border-emerald-700/50' },
  ];
  const color = colors[index % colors.length];

  // Handle both string and object insights
  const text = typeof insight === 'string' ? insight : insight.text || insight.message || JSON.stringify(insight);

  return (
    <div className={`
      flex-shrink-0 flex items-center gap-2
      px-3 py-2 rounded-lg
      border ${color.border} ${color.bg}
      max-w-[350px]
    `}>
      <Icon className={`${color.text} text-base flex-shrink-0`} />
      <p className="text-sm text-gray-300 line-clamp-2">
        {text}
      </p>
    </div>
  );
};

export default InsightsPanel;
