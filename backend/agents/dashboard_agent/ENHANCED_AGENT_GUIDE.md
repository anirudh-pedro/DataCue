# Enhanced Dashboard Agent - Production-Grade Structural Prompts

## Overview

The Enhanced Dashboard Agent uses **production-grade structural prompts** to generate high-quality dashboards with strict JSON output and SQL safety validation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced Dashboard Agent                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Dashboard Planning (Master Structural Prompt)       │
│  ─────────────────────────────────────────────────────────   │
│  Input:  Dataset schema (columns, types, row count)          │
│  Output: Dashboard plan with 6-10 chart specifications       │
│  Format: Strict JSON with no hallucinations                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Chart Building (Per Chart)                          │
│  ─────────────────────────────────────────────────────────   │
│  • Parse dimensions and metrics from spec                    │
│  • Execute pandas operations on DataFrame                    │
│  • Build Plotly figure with proper styling                   │
│  • Validate data exists and is valid                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Insights Generation                                 │
│  ─────────────────────────────────────────────────────────   │
│  • Analyze chart results and data patterns                   │
│  • Generate 3-5 actionable business insights                 │
│  • Return structured insight objects                         │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### ✅ Structural Prompts

**Master Dashboard Planner Prompt:**

- Generates 6-10 chart specifications
- Strict JSON output format
- No column hallucination
- Business-focused insights
- Priority-based chart ordering

**Chart Specification Format:**

```json
{
  "chart_id": "chart_1",
  "title": "Average Salary by Department",
  "chart_type": "bar",
  "description": "Compares average employee salaries across departments",
  "dimensions": ["department"],
  "metrics": ["AVG(salary)"],
  "queries_needed": 1,
  "priority": 1
}
```

### ✅ SQL Safety Validation

**Blocked Keywords:**

- DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
- TRUNCATE, REPLACE, MERGE, GRANT, REVOKE
- EXEC, EXECUTE, CALL, PROCEDURE, FUNCTION
- Comments (--), UNION, INTO

**Validation Rules:**

- Must start with SELECT
- No multiple statements (semicolons)
- Column names validated against schema
- Row limits applied to non-aggregated queries

### ✅ Chart Types Supported

| Chart Type    | Use Case                 | Requirements                    |
| ------------- | ------------------------ | ------------------------------- |
| **Bar**       | Categorical vs Numeric   | 1 dimension + 1 metric          |
| **Line**      | Time series / Trends     | 1 dimension + 1 metric          |
| **Pie**       | Distribution breakdown   | 1 categorical dimension         |
| **Histogram** | Numeric distribution     | 1 numeric column                |
| **Scatter**   | Correlation analysis     | 2 numeric columns               |
| **Box**       | Statistical distribution | 1-2 columns (grouping optional) |
| **Area**      | Trend over time          | 1 dimension + 1 metric          |

### ✅ Aggregation Functions

- **COUNT(\*)** - Count records
- **SUM(column)** - Sum numeric values
- **AVG(column)** - Average numeric values
- **MIN(column)** - Minimum value
- **MAX(column)** - Maximum value
- **MEDIAN(column)** - Median value

## Usage

### Basic Usage

```python
from agents.dashboard_agent import DashboardAgent

agent = DashboardAgent()

metadata = {
    "row_count": 1000,
    "column_count": 5,
    "columns": [
        {"name": "employee_id", "type": "integer"},
        {"name": "department", "type": "string"},
        {"name": "salary", "type": "float"},
        {"name": "joining_date", "type": "date"},
        {"name": "experience_years", "type": "integer"}
    ]
}

data = [...]  # List of dicts

result = agent.generate_dashboard(metadata, data)
```

### With User Prompt

```python
result = agent.generate_dashboard(
    metadata,
    data,
    user_prompt="Focus on salary analysis and department comparisons"
)
```

### Response Format

```python
{
    "status": "success",
    "dashboard": {
        "dashboard_id": "dashboard_abc123",
        "title": "Employee Workforce Analytics",
        "description": "Professional analytics with 8 visualizations",
        "charts": [
            {
                "id": "chart_1",
                "chart_id": "chart_1",
                "type": "bar",
                "title": "Average Salary by Department",
                "description": "Compares average employee salaries...",
                "figure": {
                    "data": [...],
                    "layout": {...}
                },
                "priority": 1
            },
            ...
        ]
    },
    "insights": [
        "Engineering department has 35% higher average salary than Sales",
        "75% of employees have 3-7 years of experience",
        ...
    ]
}
```

## Configuration

### Environment Variables

```bash
# Use enhanced dashboard agent (default: true)
USE_ENHANCED_DASHBOARD_AGENT=true

# Groq API key (required)
GROQ_API_KEY=your_groq_api_key_here

# LLM model (default: llama-3.3-70b-versatile)
GROQ_MODEL=llama-3.3-70b-versatile
```

### Switching Between Agents

```python
# Use enhanced agent (default)
from agents.dashboard_agent import EnhancedDashboardAgent
agent = EnhancedDashboardAgent()

# Use legacy agent
from agents.dashboard_agent.dashboard_agent import DashboardAgent
agent = DashboardAgent()
```

## Prompts Reference

### Master Dashboard Planner Prompt

```
SYSTEM: You are a senior data analyst and BI architect.
You must only return valid JSON.
Do not include explanations, markdown, or comments.
Do not hallucinate column names.
Use only the provided schema.

USER: You are given a dataset schema extracted from a CSV file.

Your task is to DESIGN a professional analytics dashboard.

DATASET SCHEMA:
{schema}

INSTRUCTIONS:
1. Generate BETWEEN 6 AND 10 dashboard charts.
2. Each chart MUST provide a meaningful business insight.
3. Avoid redundant charts.
4. Do NOT use ID or name columns as chart axes unless required.
5. Prefer aggregated insights.
6. Choose appropriate chart types only.

RETURN FORMAT:
{
  "dashboard_title": "string",
  "charts": [...]
}

ONLY RETURN VALID JSON.
```

### Insights Generation Prompt

```
SYSTEM: You are a business intelligence analyst.
Generate clear, actionable insights from data.
Return only JSON.

USER: Analyze the following data and generate 3-5 key insights.

DATASET INFO:
{metadata}

QUERY RESULTS:
{results}

Generate insights that are:
1. Specific and data-driven
2. Actionable for business users
3. Non-technical

RETURN FORMAT:
{
  "insights": [
    {
      "title": "Insight title",
      "description": "1-2 sentence explanation",
      "priority": "high|medium|low",
      "category": "trend|anomaly|comparison|distribution"
    }
  ]
}

ONLY RETURN VALID JSON.
```

## Error Handling

### Fallback Mechanisms

1. **Dashboard Planning Failure**: Falls back to basic charts using metadata
2. **Chart Building Failure**: Skips failed chart, continues with others
3. **Insights Generation Failure**: Returns basic summary insights

### Validation

All chart specifications are validated for:

- Column existence in dataset
- Valid chart type
- Required dimensions/metrics present
- Data availability

## Performance

- **Planning**: ~2-3 seconds (single LLM call)
- **Chart Building**: ~0.1-0.3 seconds per chart (parallel processing)
- **Insights**: ~1-2 seconds (single LLM call)
- **Total**: ~5-10 seconds for complete dashboard with 8 charts

## Best Practices

### 1. Provide Rich Metadata

```python
metadata = {
    "row_count": 10000,
    "column_count": 15,
    "columns": [
        {
            "name": "revenue",
            "type": "float",
            "unique_count": 8743,
            "null_count": 12,
            "min": 100.50,
            "max": 50000.00
        },
        ...
    ]
}
```

### 2. Use User Prompts for Guidance

```python
user_prompt = """
Focus on:
- Revenue trends over time
- Regional performance comparison
- Product category analysis
- Customer segmentation insights
"""
```

### 3. Limit Data Size

```python
# For large datasets, sample for dashboard generation
if len(data) > 10000:
    data_sample = random.sample(data, 10000)
else:
    data_sample = data
```

### 4. Handle Missing Data

```python
# Clean data before passing to agent
df = pd.DataFrame(data)
df = df.fillna({'numeric_col': 0, 'categorical_col': 'Unknown'})
data = df.to_dict('records')
```

## Troubleshooting

### Issue: JSON Parse Error

**Cause**: LLM returned non-JSON response

**Solution**:

```python
from agents.dashboard_agent.structured_prompts import extract_json_from_response

try:
    result = extract_json_from_response(response_text)
except ValueError:
    # Use fallback plan
    result = agent._fallback_dashboard_plan(metadata)
```

### Issue: No Charts Generated

**Cause**: All chart building failed due to data issues

**Solution**: Check data quality and column types

```python
import pandas as pd
df = pd.DataFrame(data)
print(df.dtypes)
print(df.isnull().sum())
```

### Issue: SQL Validation Failure

**Cause**: Blocked keyword detected

**Solution**: Review SQL generation prompt and add stricter rules

```python
from agents.dashboard_agent.structured_prompts import validate_sql_safety

validation = validate_sql_safety(sql_query)
if not validation["safe"]:
    logger.error(f"SQL validation failed: {validation['reason']}")
```

## Migration Guide

### From Legacy Agent

```python
# Before (legacy)
from agents.dashboard_agent import DashboardAgent
agent = DashboardAgent()

# After (enhanced - no code changes needed!)
from agents.dashboard_agent import DashboardAgent
agent = DashboardAgent()  # Automatically uses EnhancedDashboardAgent

# Or explicitly use enhanced
from agents.dashboard_agent import EnhancedDashboardAgent
agent = EnhancedDashboardAgent()
```

### Response Format Changes

The response format is **backward compatible**. All existing code will continue to work.

## Future Enhancements

- [ ] Real SQL execution against PostgreSQL (with safety validation)
- [ ] Multi-query chart support (e.g., comparison charts)
- [ ] Custom aggregation functions
- [ ] Advanced filtering and drill-down
- [ ] Export to PowerBI/Tableau format
- [ ] Real-time dashboard updates
- [ ] Chart interactions and cross-filtering

## License

Internal use only - DataCue Platform
