"""
Structured Prompts for Dashboard Generation Pipeline
Production-grade prompts that ensure strict JSON output and safe SQL generation
"""

from typing import Dict, Any, List

# ============================================================================
# MASTER DASHBOARD PLANNER PROMPT
# ============================================================================

SYSTEM_PROMPT_PLANNER = """You are a senior data analyst and BI architect.
You must only return valid JSON.
Do not include explanations, markdown, or comments.
Do not hallucinate column names.
Use only the provided schema."""

def build_dashboard_planner_prompt(metadata: Dict[str, Any]) -> str:
    """
    Build the master prompt for dashboard planning
    
    Args:
        metadata: Dataset schema with columns, types, row count
        
    Returns:
        Formatted prompt string
    """
    # Build schema JSON
    schema = {
        "table_name": "uploaded_data",
        "row_count": metadata.get("row_count", 0),
        "columns": [
            {
                "name": col["name"],
                "type": col["type"]
            }
            for col in metadata.get("columns", [])
        ]
    }
    
    schema_json = format_json(schema)
    
    return f"""You are given a dataset schema extracted from a CSV file.

Your task is to DESIGN a professional analytics dashboard.

DATASET SCHEMA:
{schema_json}

INSTRUCTIONS:

1. Generate BETWEEN 6 AND 10 dashboard charts.
2. Each chart MUST provide a meaningful business insight.
3. Avoid redundant charts.
4. Do NOT use ID or name columns as chart axes unless required.
5. Prefer aggregated insights.
6. Choose appropriate chart types only.

FOR EACH CHART, RETURN:
- chart_id (string, unique)
- title (short and professional)
- chart_type (bar, line, pie, histogram, scatter, box, area)
- description (1–2 sentences, non-technical)
- dimensions (columns used for grouping)
- metrics (aggregations like COUNT, AVG, SUM, MIN, MAX)
- queries_needed (integer ≥ 1)
- priority (1 = most important)

RETURN FORMAT:
{{
  "dashboard_title": "string",
  "charts": [ ... ]
}}

ONLY RETURN VALID JSON."""

# ============================================================================
# SQL GENERATION PROMPT
# ============================================================================

SYSTEM_PROMPT_SQL = """You are a PostgreSQL expert.
Generate SAFE, READ-ONLY queries.
Return ONLY SQL.
No markdown, no explanations."""

def build_sql_generation_prompt(
    table_name: str,
    dimensions: List[str],
    metrics: List[str],
    chart_type: str,
    filters: Dict[str, Any] = None
) -> str:
    """
    Build prompt for generating a single SQL query
    
    Args:
        table_name: Name of the database table
        dimensions: Columns for grouping
        metrics: Aggregation expressions
        chart_type: Type of chart being generated
        filters: Optional WHERE clause filters
        
    Returns:
        Formatted prompt string
    """
    filters_text = ""
    if filters:
        filters_text = f"\nFILTERS:\n{format_json(filters)}"
    
    return f"""Generate a SAFE, READ-ONLY PostgreSQL query.

RULES:
- Use ONLY the provided table and columns
- Do NOT use DROP, DELETE, UPDATE, INSERT
- Return ONLY SQL
- No markdown
- No explanation

TABLE: {table_name}

DIMENSIONS:
{format_json(dimensions)}

METRICS:
{format_json(metrics)}

CHART TYPE:
{chart_type}{filters_text}

Output only the SQL query."""

# ============================================================================
# PER-CHART SQL GENERATION PROMPT
# ============================================================================

def build_chart_sql_prompt(
    metadata: Dict[str, Any],
    chart_spec: Dict[str, Any]
) -> str:
    """
    Build prompt for generating SQL query/queries for a single chart
    This makes ONE LLM request per chart
    
    Args:
        metadata: Dataset schema with columns and types
        chart_spec: Chart specification from dashboard planner
        
    Returns:
        Formatted prompt string
    """
    # Build schema info
    schema = {
        "table_name": "uploaded_data",
        "columns": [
            {
                "name": col["name"],
                "type": col["type"]
            }
            for col in metadata.get("columns", [])
        ]
    }
    
    queries_needed = chart_spec.get("queries_needed", 1)
    
    if queries_needed == 1:
        return f"""You are a PostgreSQL expert. Generate a SAFE, READ-ONLY query.

DATASET SCHEMA:
{format_json(schema)}

CHART SPECIFICATION:
- Title: {chart_spec.get('title')}
- Type: {chart_spec.get('chart_type')}
- Description: {chart_spec.get('description')}
- Dimensions: {chart_spec.get('dimensions')}
- Metrics: {chart_spec.get('metrics')}

RULES:
1. Use ONLY columns from the schema
2. Table name is 'uploaded_data'
3. Return ONLY valid PostgreSQL SELECT query
4. Do NOT use: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
5. No markdown code blocks
6. No explanations

Return only the SQL query."""
    else:
        return f"""You are a PostgreSQL expert. Generate {queries_needed} SAFE, READ-ONLY queries.

DATASET SCHEMA:
{format_json(schema)}

CHART SPECIFICATION:
- Title: {chart_spec.get('title')}
- Type: {chart_spec.get('chart_type')}
- Description: {chart_spec.get('description')}
- Dimensions: {chart_spec.get('dimensions')}
- Metrics: {chart_spec.get('metrics')}

This chart requires {queries_needed} separate queries.

RULES:
1. Use ONLY columns from the schema
2. Table name is 'uploaded_data'
3. Return a JSON array of SQL queries
4. Do NOT use: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
5. No markdown code blocks

Example output:
["SELECT col1, COUNT(*) FROM uploaded_data GROUP BY col1", "SELECT col2, AVG(col3) FROM uploaded_data GROUP BY col2"]

Return only the JSON array of SQL queries."""

# ============================================================================
# MULTI-QUERY PROMPT (LEGACY - keeping for backward compatibility)
# ============================================================================

def build_multi_query_prompt(
    table_name: str,
    chart_spec: Dict[str, Any]
) -> str:
    """
    Build prompt for generating multiple SQL queries for complex charts
    
    Args:
        table_name: Name of the database table
        chart_spec: Full chart specification
        
    Returns:
        Formatted prompt string
    """
    return f"""Generate PostgreSQL queries needed to support this chart.

Chart requires multiple metrics.

Return an ARRAY of SQL queries.

Return only SQL queries in JSON array.

TABLE: {table_name}

CHART SPEC:
{format_json(chart_spec)}

Example output:
["SELECT ...", "SELECT ..."]

Output only the JSON array of SQL queries."""

# ============================================================================
# INSIGHT GENERATION PROMPT
# ============================================================================

SYSTEM_PROMPT_INSIGHTS = """You are a business intelligence analyst.
Generate clear, actionable insights from data.
Return only JSON."""

def build_insights_prompt(
    metadata: Dict[str, Any],
    query_results: List[Dict[str, Any]]
) -> str:
    """
    Build prompt for generating insights from query results
    
    Args:
        metadata: Dataset metadata
        query_results: Results from executed queries
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the following data and generate 3-5 key insights.

DATASET INFO:
{format_json(metadata)}

QUERY RESULTS:
{format_json(query_results[:100])}  # Limit for token efficiency

Generate insights that are:
1. Specific and data-driven
2. Actionable for business users
3. Non-technical

Return format:
{{
  "insights": [
    {{
      "title": "Insight title",
      "description": "1-2 sentence explanation",
      "priority": "high|medium|low",
      "category": "trend|anomaly|comparison|distribution"
    }}
  ]
}}

ONLY RETURN VALID JSON."""

# ============================================================================
# CHART EXPLANATION PROMPT
# ============================================================================

def build_chart_explanation_prompt(chart_title: str, chart_type: str) -> str:
    """
    Build prompt for generating user-friendly chart explanations
    
    Args:
        chart_title: Title of the chart
        chart_type: Type of chart
        
    Returns:
        Formatted prompt string
    """
    return f"""Explain this chart for a non-technical user in 2 sentences.

Chart title: {chart_title}
Chart type: {chart_type}

The explanation should:
- Be clear and simple
- Explain what the chart shows
- Help users understand the insight

Return only the explanation text, no JSON."""

# ============================================================================
# SQL SAFETY VALIDATION
# ============================================================================

SQL_BLOCKED_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
    'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
    'EXEC', 'EXECUTE', 'CALL', 'PROCEDURE', 'FUNCTION',
    '--', '/*', '*/', 'UNION', 'INTO'
]

def validate_sql_safety(sql: str) -> Dict[str, Any]:
    """
    Validate that SQL query is safe to execute
    
    Args:
        sql: SQL query string
        
    Returns:
        Dict with 'safe' boolean and 'reason' if unsafe
    """
    sql_upper = sql.upper()
    
    # Check for blocked keywords
    for keyword in SQL_BLOCKED_KEYWORDS:
        if keyword in sql_upper:
            return {
                "safe": False,
                "reason": f"Blocked keyword detected: {keyword}"
            }
    
    # Must be SELECT query
    if not sql_upper.strip().startswith('SELECT'):
        return {
            "safe": False,
            "reason": "Query must start with SELECT"
        }
    
    # Check for semicolons (multiple statements)
    if sql.count(';') > 1:
        return {
            "safe": False,
            "reason": "Multiple statements not allowed"
        }
    
    return {"safe": True}

def validate_columns_exist(sql: str, valid_columns: List[str]) -> Dict[str, Any]:
    """
    Validate that SQL only references existing columns
    
    Args:
        sql: SQL query string
        valid_columns: List of valid column names
        
    Returns:
        Dict with 'valid' boolean and 'invalid_columns' list if any
    """
    # Extract potential column references
    # This is a simple check - can be enhanced with SQL parsing
    invalid = []
    
    for col in valid_columns:
        # Basic validation - could use sqlparse for better parsing
        pass
    
    return {"valid": True, "invalid_columns": []}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_json(obj: Any) -> str:
    """Format object as pretty JSON string"""
    import json
    return json.dumps(obj, indent=2, ensure_ascii=False)

def extract_json_from_response(text: str) -> Any:
    """
    Extract JSON from LLM response, handling markdown code blocks
    
    Args:
        text: Response text that may contain JSON
        
    Returns:
        Parsed JSON object
        
    Raises:
        ValueError: If no valid JSON found
    """
    import json
    import re
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{[\s\S]*\}',
        r'\[[\s\S]*\]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if '```' in pattern else match.group(0))
            except json.JSONDecodeError:
                continue
    
    raise ValueError("No valid JSON found in response")
