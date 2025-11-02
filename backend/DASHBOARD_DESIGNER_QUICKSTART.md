# Dashboard Designer API - Quick Start Guide

## 🎯 Overview

The Dashboard Designer provides two ways to create dashboards:

1. **Template Mode**: Choose a template and customize each section
2. **AI Mode**: Let AI analyze your data and auto-generate a dashboard

## 📋 Prerequisites

1. Backend running on `http://localhost:8000`
2. Dataset uploaded via ingestion API
3. Groq API key in `.env` file (for AI mode)

## 🚀 API Endpoints

### 1. List All Templates

**Request:**

```http
GET /api/dashboard-designer/templates
```

**Response:**

```json
[
  {
    "template_id": "sales_overview",
    "name": "Sales Overview",
    "description": "Comprehensive sales performance dashboard",
    "category": "Sales",
    "icon": "💰",
    "sections": [
      {
        "section_id": "header",
        "section_type": "header",
        "title": "Dashboard Title",
        "position": 0,
        "size": "full"
      },
      {
        "section_id": "revenue_trend",
        "section_type": "chart",
        "title": "Revenue Over Time",
        "position": 4,
        "size": "large",
        "default_chart_type": "line",
        "allowed_chart_types": ["line", "area", "bar"]
      }
    ]
  }
]
```

### 2. Get Template Details

**Request:**

```http
GET /api/dashboard-designer/templates/sales_overview
```

**Response:** Single template object with all sections

### 3. Get Chart Options for Section

**Request:**

```http
POST /api/dashboard-designer/chart-options
Content-Type: application/json

{
  "dataset_id": "your_dataset_id",
  "template_id": "sales_overview",
  "section_id": "revenue_trend"
}
```

**Response:**

```json
{
  "section_id": "revenue_trend",
  "available_chart_types": ["line", "area", "bar"],
  "x_axis_options": ["date", "month", "year"],
  "y_axis_options": ["revenue", "sales", "profit"],
  "color_options": ["category", "region"],
  "aggregation_options": ["sum", "avg", "count", "min", "max"]
}
```

### 4. Configure a Dashboard Section

**Request:**

```http
POST /api/dashboard-designer/set-section
Content-Type: application/json

{
  "dataset_id": "your_dataset_id",
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
```

**Response:** Updated DashboardConfig with dashboard_id

### 5. AI Generate Dashboard

**Request:**

```http
POST /api/dashboard-designer/generate
Content-Type: application/json

{
  "dataset_id": "your_dataset_id",
  "user_prompt": "Create a sales dashboard focusing on revenue trends and product performance"
}
```

**Response:**

```json
{
  "dashboard_id": "dashboard_abc123",
  "config": {
    "dashboard_id": "dashboard_abc123",
    "template_id": "ai_generated",
    "dataset_id": "your_dataset_id",
    "title": "Sales Performance Dashboard",
    "sections": [...]
  },
  "ai_reasoning": "Generated 3 KPIs and 5 charts focusing on revenue trends, product analysis, and time series patterns..."
}
```

### 6. Get Finalized Dashboard

**Request:**

```http
GET /api/dashboard-designer/dashboard/{dashboard_id}
```

**Response:**

```json
{
  "dashboard_id": "dashboard_abc123",
  "title": "Sales Performance Dashboard",
  "description": "Comprehensive sales analysis",
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
        "x": ["2024-01", "2024-02", "2024-03"],
        "y": [100000, 120000, 150000],
        "x_label": "date",
        "y_label": "revenue"
      }
    }
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

## 📝 Usage Workflows

### Workflow 1: Template-Based Dashboard

```javascript
// 1. Get all templates
const templates = await fetch("/api/dashboard-designer/templates").then((r) =>
  r.json()
);

// 2. User selects template
const selectedTemplate = templates[0]; // e.g., sales_overview

// 3. For each chart section, get options
for (const section of selectedTemplate.sections) {
  if (section.section_type === "chart") {
    const options = await fetch("/api/dashboard-designer/chart-options", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_id: "my_dataset",
        template_id: selectedTemplate.template_id,
        section_id: section.section_id,
      }),
    }).then((r) => r.json());

    // Show options to user, let them select
    // ...
  }
}

// 4. Configure each section
const dashboardConfig = await fetch("/api/dashboard-designer/set-section", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    dataset_id: "my_dataset",
    template_id: selectedTemplate.template_id,
    section_id: "revenue_trend",
    chart_config: {
      chart_type: "line",
      x_axis: "date",
      y_axis: "revenue",
      aggregation: "sum",
    },
  }),
}).then((r) => r.json());

// 5. Get final dashboard with data
const dashboard = await fetch(
  `/api/dashboard-designer/dashboard/${dashboardConfig.dashboard_id}`
).then((r) => r.json());
```

### Workflow 2: AI-Generated Dashboard

```javascript
// 1. Upload dataset first (via ingestion API)
// ...

// 2. Generate dashboard with AI
const result = await fetch("/api/dashboard-designer/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    dataset_id: "my_dataset",
    user_prompt:
      "Create a sales dashboard with revenue trends and product analysis",
  }),
}).then((r) => r.json());

console.log("AI Reasoning:", result.ai_reasoning);

// 3. Optionally modify sections
// await fetch('/api/dashboard-designer/set-section', ...)

// 4. Get final dashboard with data
const dashboard = await fetch(
  `/api/dashboard-designer/dashboard/${result.dashboard_id}`
).then((r) => r.json());
```

## 🎨 Available Templates

1. **Sales Overview** (`sales_overview`)

   - 3 KPIs: Total Revenue, Total Orders, Avg Order Value
   - 3 Charts: Revenue Trend, Top Products, Category Distribution

2. **Data Analytics** (`data_analytics`)

   - 2 KPIs: Primary and Secondary Metrics
   - 4 Charts: Trend Analysis, Distribution, Comparison, Correlation

3. **Executive Summary** (`executive_summary`)

   - 4 KPIs: Key business metrics
   - 2 Charts: Performance Overview, Performance Breakdown

4. **Customer Insights** (`customer_insights`)

   - 2 KPIs: Total Customers, Avg Customer Value
   - 3 Charts: Customer Growth, Customer Segments, Customer Behavior

5. **Performance Metrics** (`performance_metrics`)
   - 3 KPIs: Performance metrics
   - 3 Charts: Performance Trends, Metric Comparison, Distribution

## 📊 Supported Chart Types

| Chart Type  | Use Case              | Required Axes                |
| ----------- | --------------------- | ---------------------------- |
| `bar`       | Category comparisons  | X (categorical), Y (numeric) |
| `line`      | Time series trends    | X (datetime), Y (numeric)    |
| `scatter`   | Variable correlations | X (numeric), Y (numeric)     |
| `pie`       | Proportions           | X (categorical), Y (numeric) |
| `histogram` | Data distributions    | X (numeric)                  |
| `box`       | Statistical summaries | X (categorical), Y (numeric) |
| `heatmap`   | 2D patterns           | X (any), Y (any)             |
| `area`      | Cumulative trends     | X (datetime), Y (numeric)    |
| `funnel`    | Conversion funnels    | X (categorical), Y (numeric) |
| `treemap`   | Hierarchical data     | X (categorical), Y (numeric) |

## ⚡ Tips

1. **Dataset Format**: Ensure your dataset has clear column names and proper data types
2. **AI Prompts**: Be specific about what insights you want (e.g., "focus on Q4 revenue trends")
3. **Chart Selection**: The API only shows compatible chart types based on your data
4. **Validation**: All chart configurations are validated before saving
5. **Free Tier**: AI generation uses Groq's free tier (14,400 requests/day)

## 🐛 Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid configuration or missing data
- `404 Not Found`: Template/Dashboard not found
- `500 Internal Server Error`: Server error

Error response format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

## 🔧 Testing

Use the provided test script:

```bash
cd backend
python test_dashboard_designer.py
```

All tests should pass ✅

---

**Ready to start building dashboards! 🎉**
