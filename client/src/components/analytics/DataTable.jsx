/**
 * DataTable - Tabular data display for dashboard panels
 * 
 * Features:
 * - Auto-sized columns based on content
 * - Horizontal scroll for many columns
 * - Sticky header
 * - Alternating row colors
 * - Number formatting
 * - Responsive to panel size
 */

import { useMemo } from 'react';

// Format cell value based on type
const formatCell = (value) => {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2,
    }).format(value);
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
};

// Format header text
const formatHeader = (key) => {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
};

const DataTable = ({ data, maxRows = 50 }) => {
  // Extract columns from data
  const columns = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  // Limit rows for performance
  const rows = useMemo(() => {
    if (!data) return [];
    return data.slice(0, maxRows);
  }, [data, maxRows]);

  if (!columns.length) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
      <table className="w-full text-sm border-collapse">
        <thead className="sticky top-0 z-10">
          <tr className="bg-slate-800/90 backdrop-blur-sm">
            {columns.map((col, index) => (
              <th
                key={col}
                className={`
                  px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider
                  text-slate-400 border-b border-slate-700/50
                  ${index === 0 ? 'rounded-tl-lg' : ''}
                  ${index === columns.length - 1 ? 'rounded-tr-lg' : ''}
                `}
              >
                {formatHeader(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className={`
                border-b border-slate-800/40
                transition-colors duration-150
                hover:bg-slate-800/50
                ${rowIndex % 2 === 0 ? 'bg-slate-900/20' : 'bg-transparent'}
              `}
            >
              {columns.map((col) => (
                <td
                  key={col}
                  className="px-3 py-2 text-slate-300 whitespace-nowrap"
                >
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Show row count if truncated */}
      {data && data.length > maxRows && (
        <div className="sticky bottom-0 py-2 px-3 text-xs text-slate-500 bg-slate-900/90 backdrop-blur-sm border-t border-slate-800/50">
          Showing {maxRows} of {data.length} rows
        </div>
      )}
    </div>
  );
};

export default DataTable;
