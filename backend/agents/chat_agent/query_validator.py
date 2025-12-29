"""
Query Validator Module
Ensures only safe, read-only operations are executed on datasets
"""

import re
import ast
from typing import Dict, Any, List, Set


# ============== FORBIDDEN OPERATIONS ==============
# SQL-style dangerous operations (pandas .drop() handled separately)
SQL_FORBIDDEN = {
    'delete', 'truncate', 'insert', 'update', 'alter',
    'create', 'replace', 'exec', 'execute', 'grant', 'revoke',
    'commit', 'rollback', 'merge'
}

# Python dangerous operations
PYTHON_FORBIDDEN = {
    '__import__', 'eval', 'exec', 'compile', 'open', 'input',
    'breakpoint', 'globals', 'locals', 'vars', 'dir', 'getattr',
    'setattr', 'delattr', 'hasattr'
}

# System-level dangerous operations
SYSTEM_FORBIDDEN = {
    'os', 'subprocess', 'system', 'popen', 'spawn', 'fork',
    'remove', 'rmdir', 'unlink', 'write', 'chmod', 'chown',
    'shutil', 'pathlib', 'tempfile', 'socket', 'requests', 'urllib'
}

# Pandas in-place modifications (method calls that modify data)
PANDAS_FORBIDDEN = {
    'inplace=true', 'inplace = true', 'to_csv', 'to_excel',
    'to_sql', 'to_pickle', 'to_parquet', 'to_hdf', 'to_feather',
    '.pop(', '.insert(', '.update(', 'del ',
}

# Safe methods that look like forbidden words but are OK
SAFE_METHODS = {'dropna', 'drop_duplicates', 'into'}

# ============== ALLOWED OPERATIONS ==============
ALLOWED_PANDAS_METHODS = {
    # Aggregations
    'sum', 'mean', 'median', 'std', 'var', 'min', 'max', 'count',
    'nunique', 'first', 'last', 'size', 'agg', 'aggregate',
    # Grouping
    'groupby', 'pivot_table', 'crosstab', 'value_counts',
    # Filtering
    'query', 'filter', 'where', 'mask', 'isin', 'between',
    'isna', 'notna', 'isnull', 'notnull', 'dropna',
    # Sorting
    'sort_values', 'sort_index', 'nlargest', 'nsmallest',
    # Selection
    'head', 'tail', 'sample', 'iloc', 'loc', 'at', 'iat',
    # Transformation (read-only)
    'apply', 'map', 'transform', 'pipe',
    # Reshaping (read-only)
    'reset_index', 'set_index', 'stack', 'unstack', 'melt',
    # String operations
    'str', 'contains', 'startswith', 'endswith', 'match',
    # Date operations
    'dt', 'year', 'month', 'day', 'hour', 'minute', 'second',
    # Info
    'describe', 'info', 'shape', 'columns', 'dtypes', 'index',
    # Comparison
    'eq', 'ne', 'lt', 'le', 'gt', 'ge', 'equals',
    # Math
    'abs', 'round', 'floor', 'ceil', 'clip', 'cumsum', 'cumprod',
    'diff', 'pct_change', 'rank', 'corr', 'cov',
}


class QueryValidator:
    """Validates pandas queries for safety"""
    
    def __init__(self):
        self.all_forbidden = SQL_FORBIDDEN | PYTHON_FORBIDDEN | SYSTEM_FORBIDDEN
    
    def validate(self, query: str) -> Dict[str, Any]:
        """
        Validate a query for safety
        
        Returns:
            {
                "valid": bool,
                "reason": str or None,
                "query_type": "aggregation" | "filter" | "select" | "groupby" | None
            }
        """
        if not query or not query.strip():
            return {"valid": False, "reason": "Empty query", "query_type": None}
        
        query_clean = query.strip()
        query_lower = query_clean.lower()
        
        # Check 1: Must start with 'df'
        if not query_clean.startswith('df'):
            return {
                "valid": False,
                "reason": "Query must start with 'df' (the DataFrame)",
                "query_type": None
            }
        
        # Check 2: No forbidden keywords
        for keyword in self.all_forbidden:
            # Use word boundary check to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_lower):
                return {
                    "valid": False,
                    "reason": f"Forbidden operation: '{keyword}'",
                    "query_type": None
                }
        
        # Check 3: No pandas in-place modifications
        for forbidden in PANDAS_FORBIDDEN:
            if forbidden in query_lower:
                return {
                    "valid": False,
                    "reason": f"Forbidden pandas operation: '{forbidden}'",
                    "query_type": None
                }
        
        # Check 4: No assignment operations (except within conditions)
        if self._has_assignment(query_clean):
            return {
                "valid": False,
                "reason": "Assignments are not allowed - queries must be read-only",
                "query_type": None
            }
        
        # Check 5: No dangerous attribute access
        dangerous_patterns = [
            r'__(?!init__)\w+__',  # Dunder methods except common safe ones
            r'\.to_(?!dict|list|numpy|frame|string)\w+\(',  # Export methods (allow to_dict, to_list, etc.)
            r'\bimport\s+',         # Import statements
            r'lambda.*:.*open',   # Lambda with file operations
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, query_clean):
                return {
                    "valid": False,
                    "reason": f"Dangerous pattern detected",
                    "query_type": None
                }
        
        # Check 6: Validate it looks like valid pandas
        query_type = self._detect_query_type(query_clean)
        
        return {
            "valid": True,
            "reason": None,
            "query_type": query_type
        }
    
    def _has_assignment(self, query: str) -> bool:
        """Check if query has assignment operations"""
        # Pattern: variable = something (but not ==, !=, <=, >=)
        # We need to be careful about df[df['col'] == 'value'] which is valid
        
        # Remove string literals to avoid false positives
        query_no_strings = re.sub(r'"[^"]*"', '""', query)
        query_no_strings = re.sub(r"'[^']*'", "''", query_no_strings)
        
        # Check for standalone assignment (not comparison)
        # Pattern: word = (not preceded by <, >, !, =)
        assignment_pattern = r'(?<![<>=!])\s*=\s*(?![=])'
        
        # Find all = signs
        equals_positions = [m.start() for m in re.finditer(r'=', query_no_strings)]
        
        for pos in equals_positions:
            # Check character before and after
            before = query_no_strings[pos-1] if pos > 0 else ''
            after = query_no_strings[pos+1] if pos < len(query_no_strings)-1 else ''
            
            # If it's not a comparison operator
            if before not in '<>!=' and after != '=':
                # Check if it's inside brackets (function argument like inplace=True)
                bracket_depth = query_no_strings[:pos].count('(') - query_no_strings[:pos].count(')')
                if bracket_depth > 0:
                    # It's a function argument - check if it's forbidden
                    context = query_no_strings[max(0, pos-20):pos+20].lower()
                    if 'inplace' in context:
                        return True
                else:
                    # It's a true assignment
                    return True
        
        return False
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query being performed"""
        query_lower = query.lower()
        
        if '.groupby(' in query_lower:
            return 'groupby'
        elif any(agg in query_lower for agg in ['.sum()', '.mean()', '.count()', '.min()', '.max()', '.median()']):
            return 'aggregation'
        elif '.query(' in query_lower or '[df[' in query or 'df[df' in query:
            return 'filter'
        elif '.head(' in query_lower or '.tail(' in query_lower or '.sample(' in query_lower:
            return 'select'
        elif '.describe(' in query_lower or '.info(' in query_lower:
            return 'describe'
        else:
            return 'select'


def validate_query(query: str) -> Dict[str, Any]:
    """Convenience function for query validation"""
    validator = QueryValidator()
    return validator.validate(query)
