# Dashboard Designer Agent

AI-powered template-based dashboard generation system.

## Features

### 1. **Template Library**

5 predefined dashboard templates:

- **Sales Overview**: Revenue tracking, product analysis, sales trends
- **Data Analytics**: General-purpose data exploration and analysis
- **Executive Summary**: High-level KPIs and business metrics
- **Customer Insights**: Customer behavior and segmentation
- **Performance Metrics**: KPI tracking and performance monitoring

### 2. **AI-Powered Generation**

- Uses Groq AI (Mixtral-8x7b) to analyze datasets
- Automatically selects appropriate chart types
- Generates intelligent dashboard layouts
- Provides reasoning for chart selections

### 3. **Smart Data Analysis**

- Automatically detects column types (numeric, categorical, datetime)
- Recommends compatible chart types based on data structure
- Validates chart configurations
- Suggests default axes based on data patterns

### 4. **Interactive Builder**

- Choose from predefined templates
- Customize each section independently
- Real-time validation of chart configurations
- Preview before finalizing

## API Endpoints

### GET `/api/dashboard-designer/templates`

Get all available templates

```json
Response: Array of DashboardTemplate objects
```

### GET `/api/dashboard-designer/templates/{template_id}`

Get specific template details

```json
Response: DashboardTemplate with sections
```

### POST `/api/dashboard-designer/chart-options`

Get available chart options for a section

```json
Request:
{
  "dataset_id": "dataset_123",
  "template_id": "sales_overview",
  "section_id": "revenue_trend"
}

Response:
{
  "section_id": "revenue_trend",
  "available_chart_types": ["line", "area", "bar"],
  "x_axis_options": ["date", "month", "year"],
  "y_axis_options": ["revenue", "sales", "profit"],
  "color_options": ["category", "region"],
  "aggregation_options": ["sum", "avg", "count"]
}
```

### POST `/api/dashboard-designer/set-section`

Configure a specific dashboard section

```json
Request:
{
  "dataset_id": "dataset_123",
  "template_id": "sales_overview",
  "section_id": "revenue_trend",
  "chart_config": {
    "chart_type": "line",
    "x_axis": "date",
    "y_axis": "revenue",
    "color_by": "region",
    "aggregation": "sum",
    "title": "Revenue Over Time",
    "description": "Monthly revenue trends by region"
  }
}

Response: Updated DashboardConfig
```

### POST `/api/dashboard-designer/generate`

AI-generate complete dashboard

```json
Request:
{
  "dataset_id": "dataset_123",
  "user_prompt": "Create a sales dashboard focusing on revenue and customer metrics"
}

Response:
{
  "dashboard_id": "dash_abc123",
  "config": { ... },
  "ai_reasoning": "Generated 3 KPIs and 5 charts focusing on revenue trends..."
}
```

### GET `/api/dashboard-designer/dashboard/{dashboard_id}`

Get finalized dashboard with data

```json
Response:
{
  "dashboard_id": "dash_abc123",
  "title": "Sales Overview",
  "kpis": [
    {
      "section_id": "total_revenue",
      "title": "Total Revenue",
      "value": 1234567.89,
      "description": "Sum of all revenue"
    }
  ],
  "charts": [
    {
      "section_id": "revenue_trend",
      "title": "Revenue Over Time",
      "chart_type": "line",
      "data": {
        "x": ["2024-01", "2024-02", ...],
        "y": [100000, 120000, ...],
        "x_label": "date",
        "y_label": "revenue"
      }
    }
  ]
}
```

## Supported Chart Types

| Chart Type  | Best For             | Required Axes                     |
| ----------- | -------------------- | --------------------------------- |
| `bar`       | Category comparisons | X (categorical), Y (numeric)      |
| `line`      | Time series trends   | X (datetime/numeric), Y (numeric) |
| `scatter`   | Correlations         | X (numeric), Y (numeric)          |
| `pie`       | Proportions          | X (categorical), Y (numeric)      |
| `histogram` | Distributions        | X (numeric)                       |
| `box`       | Statistical analysis | X (categorical), Y (numeric)      |
| `heatmap`   | 2D patterns          | X (any), Y (any)                  |
| `area`      | Cumulative trends    | X (datetime/numeric), Y (numeric) |
| `funnel`    | Conversion rates     | X (categorical), Y (numeric)      |
| `treemap`   | Hierarchical data    | X (categorical), Y (numeric)      |

## Usage Flow

### Template Mode

1. User selects a template from the library
2. For each section:
   - Request chart options based on dataset
   - User selects chart type and axes
   - Configure the section
3. Finalize dashboard to generate all charts

### AI Mode

1. User uploads dataset
2. Optionally provide guidance prompt
3. AI analyzes data and generates complete dashboard
4. Review and optionally modify sections
5. Finalize dashboard

## Data Requirements

- Dataset must be uploaded via the ingestion API first
- Columns are automatically typed as:
  - **Numeric**: int, float values
  - **Categorical**: strings, objects
  - **Datetime**: date/time values

## Configuration

Uses `groq_api` from `.env` file for AI generation:

```
groq_api = your_groq_api_key_here
```

## Error Handling

- Dataset validation before chart generation
- Chart type compatibility checks
- Axis type validation
- Fallback to rule-based generation if AI fails

## Files

```
backend/
├── models/
│   └── dashboard_models.py          # Pydantic models
├── agents/
│   └── dashboard_designer_agent/
│       ├── __init__.py
│       ├── template_library.py      # 5 predefined templates
│       ├── data_analyzer.py         # Smart data analysis
│       └── designer_agent.py        # AI generation
├── services/
│   └── dashboard_designer_service.py # Business logic
└── routers/
    └── dashboard_designer_router.py  # API endpoints
```

## Future Enhancements

- [ ] Custom template creation
- [ ] Template sharing/export
- [ ] Advanced chart customization (colors, fonts)
- [ ] Multi-dataset dashboards
- [ ] Real-time data updates
- [ ] Dashboard versioning
- [ ] Collaboration features
