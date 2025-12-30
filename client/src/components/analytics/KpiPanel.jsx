/**
 * KpiPanel - Key Performance Indicator display for dashboard panels
 * 
 * Features:
 * - Large primary value display
 * - Change indicator with trend arrow
 * - Optional comparison period
 * - Mini sparkline (optional)
 * - Responsive to panel size
 */

import { useMemo } from 'react';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';

// Number formatting utilities
const formatNumber = (value, options = {}) => {
  if (value === null || value === undefined) return '—';
  
  const num = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
  if (isNaN(num)) return value;

  const { compact = false, decimals = 0, prefix = '', suffix = '' } = options;

  if (compact && Math.abs(num) >= 1000) {
    const formatter = new Intl.NumberFormat('en-US', {
      notation: 'compact',
      compactDisplay: 'short',
      maximumFractionDigits: 1,
    });
    return prefix + formatter.format(num) + suffix;
  }

  const formatter = new Intl.NumberFormat('en-US', {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
  
  return prefix + formatter.format(num) + suffix;
};

const KpiPanel = ({ panel }) => {
  // Extract KPI data from panel
  const kpiData = useMemo(() => {
    // Support multiple data formats
    const { data, config } = panel;

    // Format 1: Direct value in panel
    if (panel.value !== undefined) {
      return {
        value: panel.value,
        change: panel.change,
        changeType: panel.changeType || detectChangeType(panel.change),
        previousValue: panel.previousValue,
        prefix: panel.prefix || '',
        suffix: panel.suffix || '',
        format: panel.format || 'number',
      };
    }

    // Format 2: Value in data array (aggregated result)
    if (Array.isArray(data) && data.length > 0) {
      const first = data[0];
      const keys = Object.keys(first);
      const valueKey = keys.find(k => 
        typeof first[k] === 'number' || !isNaN(parseFloat(first[k]))
      );
      
      if (valueKey) {
        return {
          value: first[valueKey],
          change: null,
          changeType: 'neutral',
          prefix: '',
          suffix: '',
          format: 'number',
        };
      }
    }

    // Format 3: Single computed value
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return {
        value: data.value || data.total || data.count || data.sum,
        change: data.change || data.delta,
        changeType: data.changeType || detectChangeType(data.change),
        previousValue: data.previousValue || data.previous,
        prefix: data.prefix || '',
        suffix: data.suffix || '',
        format: data.format || 'number',
      };
    }

    return { value: '—', change: null, changeType: 'neutral' };
  }, [panel]);

  // Determine if panel is compact (single row)
  const isCompact = (panel.layout?.h || 1) === 1;

  return (
    <div className={`
      h-full flex
      ${isCompact ? 'flex-col justify-center' : 'flex-col justify-center'}
    `}>
      {/* Title */}
      {panel.title && (
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
          {panel.title}
        </div>
      )}
      
      {/* Primary Value */}
      <div className={`
        font-bold text-gray-900 leading-none
        ${isCompact ? 'text-2xl md:text-3xl' : 'text-4xl mb-2'}
      `}>
        {formatNumber(kpiData.value, {
          compact: true,
          prefix: kpiData.prefix,
          suffix: kpiData.suffix,
        })}
      </div>

      {/* Change Indicator */}
      {kpiData.change !== null && kpiData.change !== undefined && (
        <ChangeIndicator 
          change={kpiData.change} 
          type={kpiData.changeType}
          isCompact={isCompact}
        />
      )}

      {/* Previous Value or Subtitle */}
      {(kpiData.previousValue || panel.subtitle) && (
        <div className="text-xs text-gray-500 mt-1">
          {kpiData.previousValue 
            ? `vs ${formatNumber(kpiData.previousValue, { compact: true })} previous`
            : panel.subtitle
          }
        </div>
      )}
    </div>
  );
};

/**
 * Change indicator with trend arrow and color
 */
const ChangeIndicator = ({ change, type, isCompact }) => {
  const numericChange = typeof change === 'string' 
    ? parseFloat(change.replace(/[%,]/g, '')) 
    : change;

  const changeType = type || detectChangeType(numericChange);
  
  const config = {
    positive: {
      icon: FiTrendingUp,
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
    },
    negative: {
      icon: FiTrendingDown,
      bg: 'bg-rose-50',
      text: 'text-rose-600',
      border: 'border-rose-200',
    },
    neutral: {
      icon: FiMinus,
      bg: 'bg-gray-50',
      text: 'text-gray-500',
      border: 'border-gray-200',
    },
  };

  const { icon: Icon, bg, text, border } = config[changeType] || config.neutral;
  
  const displayValue = typeof change === 'string' 
    ? change 
    : `${numericChange >= 0 ? '+' : ''}${numericChange.toFixed(1)}%`;

  return (
    <div className={`
      inline-flex items-center gap-1
      px-2 py-1 rounded-full
      border ${border} ${bg}
      ${isCompact ? 'text-xs' : 'text-sm'}
    `}>
      <Icon className={`${text} ${isCompact ? 'text-xs' : 'text-sm'}`} />
      <span className={text}>{displayValue}</span>
    </div>
  );
};

/**
 * Auto-detect change type from value
 */
function detectChangeType(change) {
  if (change === null || change === undefined) return 'neutral';
  
  const num = typeof change === 'string' 
    ? parseFloat(change.replace(/[%,]/g, '')) 
    : change;
  
  if (isNaN(num)) return 'neutral';
  if (num > 0) return 'positive';
  if (num < 0) return 'negative';
  return 'neutral';
}

export default KpiPanel;
