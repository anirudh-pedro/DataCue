# Modular Dashboard - Architecture Guide

## Overview

The new modular dashboard system uses AI to intelligently generate and populate visualization components based on your dataset. Instead of predefined charts, it analyzes your data schema and creates relevant visualizations dynamically.

## Architecture Flow

```
CSV Upload → MongoDB Storage
     ↓
Dataset Schema → Groq LLM → Component Suggestions
     ↓
For Each Component:
  Component Config → Groq LLM → MongoDB Query → Execute → Render
```

## Key Components

### Frontend

#### 1. **ModularDashboard.jsx** (`client/src/pages/`)

Main dashboard page that orchestrates the entire flow:

- Accepts `session_id` and `dataset_id`
- Fetches component suggestions from backend
- Loads data for each component
- Renders the dashboard grid

#### 2. **DashboardGrid.jsx** (`client/src/components/dashboard/`)

Layout manager for visualization blocks:

- Responsive grid layout
- Loading states
- Empty states
- Component expansion

#### 3. **VisualizationBlock.jsx** (`client/src/components/dashboard/`)

Individual visualization component:

- Supports multiple types: `metric`, `chart`, `pie`, `table`
- Expand/minimize functionality
- Refresh capability
- Plotly.js integration for charts

### Backend

#### 1. **DashboardOrchestrationService** (`backend/services/`)

Generates component suggestions using Groq:

- Analyzes dataset schema (columns, types)
- Considers sample data for context
- Returns structured component configurations
- Fallback to rule-based suggestions if LLM fails

#### 2. **ComponentQueryService** (`backend/services/`)

Generates MongoDB queries for each component:

- Takes component requirements
- Generates appropriate aggregation pipelines
- Adds security filters (session_id, dataset_id)
- Handles different visualization types

#### 3. **Dashboard Router** (`backend/routers/dashboard_router.py`)

New endpoints:

- `POST /dashboard/suggest-components` - Get component suggestions
- `POST /dashboard/component-data` - Get data for specific component

## API Endpoints

### 1. Suggest Components

**Endpoint:** `POST /dashboard/suggest-components`

**Request:**

```json
{
  "session_id": "user123",
  "dataset_id": "dataset_xyz",
  "max_components": 6
}
```

**Response:**

```json
{
  "success": true,
  "session_id": "user123",
  "dataset_id": "dataset_xyz",
  "components": [
    {
      "id": "revenue_metric",
      "title": "Total Revenue",
      "description": "Sum of all revenue",
      "visualizationType": "metric",
      "chartType": null,
      "purpose": "Show total revenue at a glance",
      "requiredColumns": ["revenue"],
      "aggregation": "sum"
    },
    {
      "id": "sales_trend",
      "title": "Sales Over Time",
      "description": "Monthly sales trend",
      "visualizationType": "chart",
      "chartType": "line",
      "purpose": "Track sales performance",
      "requiredColumns": ["date", "sales"],
      "aggregation": "sum"
    }
  ],
  "total_components": 2
}
```

### 2. Get Component Data

**Endpoint:** `POST /dashboard/component-data`

**Request:**

```json
{
  "session_id": "user123",
  "dataset_id": "dataset_xyz",
  "component": {
    "id": "revenue_metric",
    "visualizationType": "metric",
    "requiredColumns": ["revenue"],
    "aggregation": "sum"
  }
}
```

**Response:**

```json
{
  "success": true,
  "component_id": "revenue_metric",
  "data": [
    {
      "revenue": 1500000,
      "count": 1250
    }
  ],
  "pipeline": [
    { "$match": { "session_id": "user123", "dataset_id": "dataset_xyz" } },
    {
      "$group": {
        "_id": null,
        "revenue": { "$sum": "$revenue" },
        "count": { "$sum": 1 }
      }
    },
    { "$project": { "_id": 0 } }
  ],
  "row_count": 1
}
```

## Component Types

### 1. Metric

Display key numbers (totals, averages, counts):

```json
{
  "visualizationType": "metric",
  "data": {
    "metrics": [
      { "label": "TOTAL REVENUE", "value": 1500000 },
      { "label": "AVG ORDER", "value": 1200, "change": 5.2 }
    ]
  }
}
```

### 2. Chart (Bar/Line/Histogram)

Display trends and distributions:

```json
{
  "visualizationType": "chart",
  "chartType": "line",
  "data": {
    "figure": {
      "data": [{"type": "line", "x": [...], "y": [...]}],
      "layout": {...}
    }
  }
}
```

### 3. Pie Chart

Display proportions:

```json
{
  "visualizationType": "pie",
  "data": {
    "figure": {
      "data": [{"type": "pie", "labels": [...], "values": [...]}],
      "layout": {...}
    }
  }
}
```

### 4. Table

Display raw data:

```json
{
  "visualizationType": "table",
  "data": {
    "rows": [
      { "name": "Product A", "sales": 1500, "profit": 450 },
      { "name": "Product B", "sales": 2200, "profit": 660 }
    ]
  }
}
```

## Usage

### From Chat Page

1. Upload CSV file
2. Click "Smart Dashboard" button when analysis completes
3. Dashboard auto-generates with session_id and dataset_id

### Direct Access

1. Navigate to `/modular-dashboard`
2. Enter session_id and optionally dataset_id
3. Click "Generate Dashboard"

## Environment Variables

Requires same configuration as MongoDB Query System:

```env
# Backend .env
GROQ_API_KEY=your_groq_api_key
MONGO_URI=mongodb://localhost:27017/datacue
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.3
```

## Benefits

1. **Intelligent**: AI analyzes your data and suggests relevant visualizations
2. **Flexible**: Each component fetched independently, no rigid structure
3. **Scalable**: Add/remove components dynamically
4. **Interactive**: Expand, refresh, customize individual components
5. **MongoDB-Powered**: Leverages aggregation framework for efficient queries

## Future Enhancements

- [ ] Drag-and-drop component reordering
- [ ] Save/load custom dashboard layouts
- [ ] Real-time data updates via WebSockets
- [ ] Export dashboard to PDF/PNG
- [ ] Share dashboard via unique URL
- [ ] Custom date range filters
- [ ] Component interaction (click to filter others)

## Troubleshooting

**No components generated:**

- Verify Groq API key is valid
- Check dataset has columns in MongoDB
- Review backend logs for LLM errors

**Empty visualizations:**

- Check MongoDB has data for session_id/dataset_id
- Verify column names match those in suggestions
- Review generated pipeline in browser console

**Slow loading:**

- Reduce max_components from 6 to 3-4
- Ensure MongoDB has indexes on session_id and dataset_id
- Check network tab for bottlenecks
