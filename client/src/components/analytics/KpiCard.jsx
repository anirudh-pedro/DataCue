/**
 * KpiCard - Professional KPI card matching Power BI dashboard style
 */

import { FiDollarSign, FiUsers, FiTrendingUp, FiPackage, FiActivity, FiTarget, FiShoppingCart, FiPercent, FiBarChart2 } from 'react-icons/fi';

// Power BI-style accent colors
const accentColors = [
  { accent: '#118DFF', bg: 'rgba(17, 141, 255, 0.15)' }, // Blue
  { accent: '#12B5CB', bg: 'rgba(18, 181, 203, 0.15)' }, // Teal
  { accent: '#E66C37', bg: 'rgba(230, 108, 55, 0.15)' }, // Orange
  { accent: '#B845A7', bg: 'rgba(184, 69, 167, 0.15)' }, // Purple
];

// Icon mapping based on common KPI titles
const getIconForKpi = (title, index) => {
  const titleLower = (title || '').toLowerCase();
  
  if (titleLower.includes('sales') || titleLower.includes('revenue') || titleLower.includes('price') || titleLower.includes('amount') || titleLower.includes('total')) {
    return FiDollarSign;
  }
  if (titleLower.includes('customer') || titleLower.includes('user') || titleLower.includes('employee') || titleLower.includes('count')) {
    return FiUsers;
  }
  if (titleLower.includes('order') || titleLower.includes('purchase')) {
    return FiShoppingCart;
  }
  if (titleLower.includes('product') || titleLower.includes('item') || titleLower.includes('unit') || titleLower.includes('quantity')) {
    return FiPackage;
  }
  if (titleLower.includes('growth') || titleLower.includes('increase') || titleLower.includes('trend') || titleLower.includes('avg')) {
    return FiTrendingUp;
  }
  if (titleLower.includes('rate') || titleLower.includes('percent') || titleLower.includes('ratio')) {
    return FiPercent;
  }
  if (titleLower.includes('target') || titleLower.includes('goal')) {
    return FiTarget;
  }
  
  // Fallback icons by index
  const fallbackIcons = [FiBarChart2, FiActivity, FiTarget, FiTrendingUp];
  return fallbackIcons[index % fallbackIcons.length];
};

// Format number with appropriate suffix
const formatValue = (value) => {
  if (value === null || value === undefined) return '—';
  
  const num = typeof value === 'string' ? parseFloat(value.replace(/[,$]/g, '')) : value;
  if (isNaN(num)) return value;
  
  if (Math.abs(num) >= 1000000000) {
    return `${(num / 1000000000).toFixed(2)}bn`;
  }
  if (Math.abs(num) >= 1000000) {
    return `${(num / 1000000).toFixed(2)}M`;
  }
  if (Math.abs(num) >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  if (Number.isInteger(num)) {
    return num.toLocaleString();
  }
  return num.toFixed(2);
};

const KpiCard = ({ kpi, index = 0 }) => {
  const Icon = getIconForKpi(kpi.title, index);
  const colorTheme = accentColors[index % accentColors.length];
  
  // Extract value
  const value = kpi.value ?? kpi.data?.[0]?.[Object.keys(kpi.data?.[0] || {})[0]] ?? '—';
  const title = kpi.title || 'Metric';

  return (
    <div className="bg-[#161b22] rounded-lg border border-gray-800/50 p-4 hover:border-gray-600/50 transition-all">
      {/* Icon and Title Row */}
      <div className="flex items-center gap-2.5 mb-3">
        <div 
          className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: colorTheme.bg }}
        >
          <Icon className="text-lg" style={{ color: colorTheme.accent }} />
        </div>
        <span className="text-xs text-gray-400 uppercase tracking-wider font-medium truncate">
          {title}
        </span>
      </div>
      
      {/* Large Value */}
      <p 
        className="text-3xl md:text-4xl font-bold tracking-tight"
        style={{ color: colorTheme.accent }}
      >
        {formatValue(value)}
      </p>
    </div>
  );
};

export default KpiCard;
