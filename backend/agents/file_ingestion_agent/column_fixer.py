"""
Column Fixer Module
Uses Groq LLM to generate meaningful column names for invalid/missing columns
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class ColumnFixer:
    """
    Uses LLM to fix invalid, missing, or duplicate column names
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = "llama-3.3-70b-versatile"
    
    def fix_columns(
        self, 
        columns: List[str], 
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix column names that are missing, duplicated, or invalid
        
        Args:
            columns: List of current column names
            sample_data: First few rows of data for context
            
        Returns:
            Dictionary with fixed columns and changes made
        """
        issues = self._identify_issues(columns)
        
        if not issues["has_issues"]:
            return {
                "fixed": False,
                "columns": columns,
                "changes": []
            }
        
        # If LLM available, use it for smart fixing
        if self.client and issues["columns_needing_fix"]:
            fixed_columns = self._fix_with_llm(columns, sample_data, issues)
        else:
            # Fallback to rule-based fixing
            fixed_columns = self._fix_with_rules(columns, issues)
        
        changes = [
            {"original": old, "fixed": new}
            for old, new in zip(columns, fixed_columns)
            if old != new
        ]
        
        return {
            "fixed": True,
            "columns": fixed_columns,
            "changes": changes,
            "issues_found": issues
        }
    
    def _identify_issues(self, columns: List[str]) -> Dict[str, Any]:
        """Identify columns with issues"""
        issues = {
            "has_issues": False,
            "missing_names": [],
            "duplicates": [],
            "invalid_names": [],
            "columns_needing_fix": []
        }
        
        seen = {}
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            
            # Check for missing/empty names
            if not col_str or col_str.lower() in ['unnamed', 'nan', 'none', '']:
                issues["missing_names"].append(i)
                issues["columns_needing_fix"].append(i)
                issues["has_issues"] = True
            
            # Check for duplicates
            elif col_str.lower() in seen:
                issues["duplicates"].append(i)
                issues["columns_needing_fix"].append(i)
                issues["has_issues"] = True
            
            # Check for invalid names (only special chars, starts with number)
            elif not re.match(r'^[a-zA-Z_]', col_str) or re.match(r'^[\d\W]+$', col_str):
                issues["invalid_names"].append(i)
                issues["columns_needing_fix"].append(i)
                issues["has_issues"] = True
            
            seen[col_str.lower()] = i
        
        return issues
    
    def _fix_with_llm(
        self, 
        columns: List[str], 
        sample_data: List[Dict[str, Any]],
        issues: Dict[str, Any]
    ) -> List[str]:
        """Use LLM to generate meaningful column names"""
        try:
            # Build context for LLM
            problem_indices = issues["columns_needing_fix"]
            
            # Get sample values for problem columns
            sample_values = {}
            for idx in problem_indices:
                col_name = columns[idx]
                values = [str(row.get(col_name, ""))[:50] for row in sample_data[:5] if row.get(col_name)]
                sample_values[idx] = values
            
            prompt = f"""You are a data analyst. I have a dataset with some problematic column names.

Current columns: {columns}

Problem columns (indices): {problem_indices}
- Missing names: {issues['missing_names']}
- Duplicate names: {issues['duplicates']}
- Invalid names: {issues['invalid_names']}

Sample values for problem columns:
{sample_values}

Generate meaningful, descriptive column names for the problem columns based on the sample data.
Use snake_case format (lowercase with underscores).

Respond with ONLY a JSON object mapping column index to new name:
{{"0": "customer_id", "3": "order_date"}}

Only include columns that need fixing."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            import json
            response_text = response.choices[0].message.content.strip()
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                fixes = json.loads(json_match.group())
                
                # Apply fixes
                fixed_columns = columns.copy()
                for idx_str, new_name in fixes.items():
                    idx = int(idx_str)
                    if 0 <= idx < len(fixed_columns):
                        fixed_columns[idx] = new_name
                
                return fixed_columns
            
        except Exception as e:
            logger.warning(f"LLM column fixing failed: {e}, using rule-based fallback")
        
        return self._fix_with_rules(columns, issues)
    
    def _fix_with_rules(self, columns: List[str], issues: Dict[str, Any]) -> List[str]:
        """Rule-based column name fixing"""
        fixed = columns.copy()
        used_names = set()
        
        for i, col in enumerate(fixed):
            col_str = str(col).strip()
            
            # Handle missing names
            if i in issues["missing_names"]:
                fixed[i] = f"column_{i + 1}"
            
            # Handle invalid names
            elif i in issues["invalid_names"]:
                # Clean the name
                clean = re.sub(r'[^\w]', '_', col_str)
                clean = re.sub(r'^[\d_]+', '', clean)
                fixed[i] = clean if clean else f"column_{i + 1}"
            
            # Handle duplicates
            elif i in issues["duplicates"]:
                base_name = col_str.lower()
                counter = 1
                new_name = f"{base_name}_{counter}"
                while new_name in used_names:
                    counter += 1
                    new_name = f"{base_name}_{counter}"
                fixed[i] = new_name
            
            used_names.add(fixed[i].lower())
        
        return fixed
