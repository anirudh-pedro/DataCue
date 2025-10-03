# Dashboard Generator Agent

## Overview

The **Dashboard Generator Agent** is the second component of the DataCue AI-powered data analysis platform. It automatically creates intelligent, interactive dashboard configurations from data processed by the File Ingestion Agent.

> **Phase 2 Update**: Now includes scatter plots with auto-correlation, intelligent chart recommendations, cross-filtering, drill-down capabilities, and full user customization!

## Features

### 🎨 Intelligent Chart Generation

- **KPI Cards**: Automatically generates summary metrics for numerical measures
- **Histograms**: Distribution analysis for numeric columns
- **Bar Charts**: Categorical data visualization
- **Time Series**: Trend analysis for temporal data
- **Scatter Plots** ⭐ _NEW_: Numeric vs numeric with auto-correlation analysis and trendlines
- **Correlation Heatmaps**: Relationship analysis between numeric variables
- **Grouped Bar Charts**: Multi-dimensional comparisons
- **Pie Charts**: Proportional distribution visualization
- **Box Plots**: Statistical distribution with outlier detection

### 🧠 Chart Recommendation Engine ⭐ _NEW_

- **Rule-Based Recommendations**: Suggests optimal chart types based on column characteristics
- **Single Column Analysis**: Best visualizations for individual columns
- **Column Pair Analysis**: Relationship-based chart suggestions (e.g., scatter for numeric pairs)
- **Full Dashboard Planning**: Complete chart suite recommendations with priority ranking
- **Confidence Scoring**: Each recommendation includes confidence level and reasoning

### � Cross-Filtering & Drill-Down ⭐ _NEW_

- **Interactive Charts**: Click a bar → filter all other charts (Tableau-style)
- **Drill-Down Support**: Click to zoom into time periods or category details
- **Cross-Filter Configuration**: JSON schema defines interactivity per chart
- **Click Actions**: `filter_category`, `filter_range`, `filter_date_range`, `show_scatter`
- **Frontend Integration**: Ready for React + Plotly.js event handling

### ⚙️ User Customization ⭐ _NEW_

- **Hide Charts**: Remove unwanted visualizations
- **Reorder Charts**: Custom dashboard layout by drag-and-drop (frontend)
- **Change Chart Types**: Override auto-generated chart types
- **Hide Filters**: Customize filter sidebar
- **Layout Preferences**: Grid columns, sidebar visibility, theme (light/dark)
- **Preference Persistence**: Save/load user preferences to JSON backend
- **Validation**: Automatic preference validation before applying

### �🔍 Smart Filtering

- **Dropdown Filters**: Multi-select filters for categorical dimensions
- **Date Range Filters**: Time-based data filtering
- **Range Sliders**: Numeric range selection

### 📐 Responsive Layout Management

- **Bootstrap-style Grid System**: 12-column responsive layout
- **Breakpoints**: Support for xs, sm, md, lg, xl, xxl screen sizes
- **Intelligent Positioning**: Charts automatically arranged by type and importance
- **Sidebar Filters**: Collapsible filter panel for better UX

### ✅ Data Quality Integration

- **Quality Scoring**: 0-100 data quality score display
- **Component Breakdown**: Completeness, uniqueness, consistency, validity metrics
- **Visual Warnings**: Alerts for low-quality data (<70% score)

## Architecture

```
dashboard_generator_agent/
├── __init__.py                    # Module exports
├── dashboard_generator.py         # Main orchestrator
├── chart_factory.py              # Chart generation logic (9 chart types)
├── layout_manager.py             # Layout and positioning
├── chart_recommender.py          # 🆕 Recommendation engine
└── customization_manager.py      # 🆕 User preferences handler
```

## Usage

### Basic Example

```python
from agents.dashboard_generator_agent import DashboardGenerator
import pandas as pd

# Initialize generator
generator = DashboardGenerator()

# Generate dashboard from ingested data
dashboard_config = generator.generate_dashboard(
    data=dataframe,           # Cleaned DataFrame
    metadata=metadata_dict    # Metadata from File Ingestion Agent
)

# Access generated components
charts = dashboard_config['charts']
filters = dashboard_config['filters']
layout = dashboard_config['layout']
```

### Dashboard Configuration Output

The generator returns a JSON-serializable dictionary:

```json
{
  "status": "success",
  "dashboard_id": "dashboard_bc7f0025",
  "title": "Data Analysis Dashboard",
  "summary": {...},
  "layout": {
    "grid_columns": 12,
    "sections": [...],
    "responsive_config": {...}
  },
  "charts": [
    {
      "id": "hist_sales_amount",
      "type": "histogram",
      "title": "Distribution of Sales Amount",
      "column": "sales_amount",
      "figure": {...},  // Plotly figure JSON
      "insights": {...}
    }
  ],
  "filters": [
    {
      "id": "filter_product_category",
      "type": "dropdown",
      "column": "product_category",
      "label": "Product Category",
      "options": ["Electronics", "Clothing", ...]
    }
  ],
  "quality_indicators": {
    "overall_score": 95.0,
    "rating": "excellent",
    "components": {...}
  }
}
```

## Phase 2 Features (NEW!)

### Scatter Plots with Auto-Correlation

```python
# Scatter plots are automatically generated for numeric column pairs
# Example output:
{
  "id": "scatter_age_income",
  "type": "scatter",
  "title": "Income vs Age",
  "columns": {"x": "age", "y": "income"},
  "insights": {
    "correlation": 0.947,
    "correlation_strength": "strong",
    "correlation_direction": "positive",
    "interpretation": "Strong positive relationship"
  },
  "interactivity": {
    "supports_drill_down": True,
    "cross_filter_enabled": True,
    "click_action": "filter_other_charts"
  }
}
```

### Chart Recommendation Engine

```python
from agents.dashboard_generator_agent import ChartRecommendationEngine

recommender = ChartRecommendationEngine()

# Get recommendations for single column
recs = recommender.recommend_for_single_column(
    "sales_amount",
    {"type": "int64", "unique_count": 1000}
)
# Returns: [{"chart_type": "histogram", "confidence": 0.9, "reason": "..."}]

# Get recommendations for column pair
recs = recommender.recommend_for_column_pair(
    "age", "income",
    age_metadata, income_metadata
)
# Returns: [{"chart_type": "scatter", "confidence": 0.75, "reason": "..."}]

# Get full dashboard recommendations
recs = recommender.recommend_dashboard_charts(
    columns_metadata,
    max_charts=10
)
```

### Cross-Filtering & Drill-Down

All charts now include interactivity configuration:

```json
{
  "interactivity": {
    "supports_drill_down": true,
    "cross_filter_enabled": true,
    "cross_filter_column": "product_category",
    "click_action": "filter_category",
    "drill_down_config": {
      "enabled": true,
      "target_column": "product_category",
      "action": "Click a bar to filter all other charts"
    }
  }
}
```

**Click Actions**:

- `filter_category`: Bar/pie chart clicks filter by category
- `filter_range`: Histogram clicks filter by value range
- `filter_date_range`: Time series clicks zoom into time period
- `show_scatter`: Heatmap cell clicks show scatter plot

### User Customization

```python
from agents.dashboard_generator_agent import DashboardCustomizer

customizer = DashboardCustomizer(storage_backend="prefs.json")

# Create preference template
template = customizer.create_preference_template(dashboard_config)

# Define user preferences
user_prefs = {
    "version": "1.0",
    "user_id": "user123",
    "hidden_charts": ["kpi_sales_amount"],  # Hide specific charts
    "chart_order": ["chart_2", "chart_1", "chart_3"],  # Reorder
    "chart_type_overrides": {
        "hist_age": "box_plot"  # Change histogram to box plot
    },
    "hidden_filters": ["filter_region"],
    "layout_preferences": {
        "grid_columns": 12,
        "hide_sidebar": False,
        "theme": "dark"
    }
}

# Apply customizations
customized = customizer.apply_user_preferences(dashboard_config, user_prefs)

# Save preferences
customizer.save_preferences(dashboard_id, user_id, user_prefs)

# Load preferences
prefs = customizer.load_preferences(dashboard_id, user_id)

# Validate preferences
errors = customizer.validate_preferences(user_prefs, dashboard_config)
```

## Chart Types

### 1. KPI Cards

- **Purpose**: Display key metrics at a glance
- **Best For**: Total sales, average values, max/min metrics
- **Generated For**: Measure columns (suggested_role: "measure")

### 2. Histograms

- **Purpose**: Show distribution of numeric data
- **Best For**: Age distribution, price ranges, score distributions
- **Generated For**: Numeric columns with histogram recommendation

### 3. Bar Charts

- **Purpose**: Compare categorical data
- **Best For**: Product categories, regions, departments
- **Generated For**: Low-cardinality dimensions (<50 unique values)

### 4. Scatter Plots ⭐ _NEW_

- **Purpose**: Analyze relationship between two numeric variables
- **Best For**: Age vs income, price vs demand, feature correlations
- **Generated For**: Numeric column pairs with correlation analysis
- **Special Features**:
  - Auto-calculates Pearson correlation coefficient
  - Adds trendline for strong correlations (|r| > 0.5)
  - Provides correlation strength (weak/moderate/strong)
  - Supports color coding by categorical variable

### 5. Time Series

- **Purpose**: Visualize trends over time
- **Best For**: Sales over time, user growth, stock prices
- **Generated For**: Data with time_dimension columns

### 6. Grouped Bar Charts

- **Purpose**: Multi-dimensional comparison
- **Best For**: Sales by category and region, performance by team and quarter
- **Generated For**: Measure vs dimension combinations

### 7. Correlation Heatmap

- **Purpose**: Show relationships between numeric variables
- **Best For**: Feature correlation, multivariate analysis
- **Generated For**: Datasets with 2+ numeric columns

## Filter Types

### Dropdown Filters

```json
{
  "type": "dropdown",
  "column": "product_category",
  "label": "Product Category",
  "multi_select": true,
  "default": "all"
}
```

### Date Range Filters

```json
{
  "type": "date_range",
  "column": "order_date",
  "label": "Date Range",
  "default": "all"
}
```

### Range Sliders

```json
{
  "type": "range_slider",
  "column": "price",
  "label": "Price Range",
  "min": 0,
  "max": 1000,
  "default": [0, 1000]
}
```

## Layout System

### Grid Configuration

- **12-column grid**: Similar to Bootstrap framework
- **Responsive breakpoints**:
  - xs: 0-575px (mobile)
  - sm: 576-767px (tablet portrait)
  - md: 768-991px (tablet landscape)
  - lg: 992-1199px (desktop)
  - xl: 1200-1399px (large desktop)
  - xxl: 1400px+ (extra large)

### Chart Sizing

- **Full Width**: Time series, correlation heatmaps (12 columns)
- **Half Width**: Histograms, box plots (6 columns)
- **Third Width**: Pie charts, KPIs (4 columns)

### Section Order

1. **KPI Row**: Key metrics at the top
2. **Filter Sidebar**: Left sidebar (3 columns on md+)
3. **Charts Grid**: Main content area (9 columns on md+)

## Integration with File Ingestion Agent

The Dashboard Generator expects metadata in this format:

```json
{
  "filename": "sales_data.csv",
  "total_rows": 1000,
  "total_columns": 6,
  "columns_metadata": {
    "sales_amount": {
      "type": "int64",
      "mean": 550.0,
      "median": 548.5,
      "chart_recommendations": ["histogram", "box_plot"],
      "suggested_role": "measure"
    },
    "product_category": {
      "type": "object",
      "unique_count": 4,
      "chart_recommendations": ["bar_chart", "pie_chart"],
      "suggested_role": "dimension"
    },
    "order_date": {
      "type": "datetime64[ns]",
      "is_time_series": true,
      "suggested_role": "time_dimension"
    }
  },
  "data_quality_score": 95.0,
  "quality_components": {...},
  "correlation_analysis": {...}
}
```

## Frontend Integration

### React + Plotly.js Example

```javascript
import React from "react";
import Plot from "react-plotly.js";

function Dashboard({ config }) {
  return (
    <div className="dashboard">
      {/* Render filters */}
      <aside className="filters">
        {config.filters.map((filter) => (
          <FilterComponent key={filter.id} {...filter} />
        ))}
      </aside>

      {/* Render charts */}
      <main className="charts-grid">
        {config.charts.map((chart) => (
          <div key={chart.id} className="chart-container">
            <h3>{chart.title}</h3>
            <Plot data={chart.figure.data} layout={chart.figure.layout} />
          </div>
        ))}
      </main>
    </div>
  );
}
```

## Testing

Run the test suite:

```bash
python test_dashboard_generator.py
```

Expected output:

```
============================================================
DASHBOARD GENERATOR AGENT - TEST
============================================================

✓ Created dataset with 100 rows and 6 columns
✓ Dashboard Generator initialized
✓ Dashboard generation complete

📊 CHARTS GENERATED: 10
🔍 FILTERS GENERATED: 5
✓ DATA QUALITY SCORE: 95.0%
```

## Dependencies

```
plotly==5.24.1
pandas==2.3.2
numpy==2.3.3
```

## Future Enhancements

### Planned Features

- [ ] **AI-Powered Chart Selection**: LLM-based chart type recommendations
- [ ] **Custom Themes**: Dark mode, high contrast, corporate themes
- [ ] **Export Capabilities**: PDF, PNG, interactive HTML export
- [ ] **Real-time Updates**: WebSocket support for live dashboards
- [ ] **Advanced Analytics**: Statistical tests, forecasting, anomaly detection
- [ ] **Dashboard Templates**: Industry-specific templates (sales, finance, HR)
- [ ] **Collaborative Features**: Comments, annotations, sharing

## API Reference

### DashboardGenerator Class

#### `generate_dashboard(data, metadata, dashboard_type="auto")`

Generates complete dashboard configuration.

**Parameters:**

- `data` (pd.DataFrame): Cleaned dataset
- `metadata` (dict): Metadata from File Ingestion Agent
- `dashboard_type` (str): "auto", "overview", "detailed", "executive"

**Returns:**

- `dict`: Dashboard configuration with charts, filters, layout

### ChartFactory Class

#### `create_histogram(data, column, metadata)`

Creates histogram for numeric distribution.

#### `create_bar_chart(data, column, metadata)`

Creates bar chart for categorical data.

#### `create_scatter_plot(data, x_column, y_column, color_column=None)` ⭐ _NEW_

Creates scatter plot with auto-correlation analysis.

**Returns:**

- Scatter plot with correlation coefficient, trendline, and insights

#### `create_time_series(data, time_column, value_column)`

Creates time series line chart.

#### `create_correlation_heatmap(data, correlation_data)`

Creates correlation heatmap.

### ChartRecommendationEngine Class ⭐ _NEW_

#### `recommend_for_single_column(column_name, metadata)`

Recommends chart types for a single column.

**Returns:**

- List of recommendations with chart type, confidence, and reasoning

#### `recommend_for_column_pair(x_column, y_column, x_metadata, y_metadata)`

Recommends chart types for column pairs.

#### `recommend_dashboard_charts(columns_metadata, max_charts=10)`

Recommends complete dashboard chart suite.

### DashboardCustomizer Class ⭐ _NEW_

#### `apply_user_preferences(dashboard_config, user_preferences)`

Applies user customizations to dashboard.

#### `save_preferences(dashboard_id, user_id, preferences)`

Saves user preferences to storage backend.

#### `load_preferences(dashboard_id, user_id)`

Loads saved user preferences.

#### `create_preference_template(dashboard_config)`

Creates customization template for users.

#### `validate_preferences(preferences, dashboard_config)`

Validates user preferences against dashboard.

### LayoutManager Class

#### `create_layout(charts, filters, kpis=None)`

Creates responsive dashboard layout.

#### `optimize_layout(charts, preferences=None)`

Optimizes chart order and grouping.

## Dependencies

```
plotly==5.24.1         # Interactive visualizations
pandas==2.3.2          # Data manipulation
numpy==2.3.3          # Numerical operations
scipy==1.14.1         # Statistical analysis (for scatter trendlines) ⭐ NEW
```

## Testing

### Run Basic Tests

```bash
python test_dashboard_generator.py
```

### Run Phase 2 Feature Tests ⭐ NEW

```bash
python test_phase2_features.py
```

Expected Phase 2 output:

```
✓ Generated 2 scatter plot(s) with correlation analysis
✓ Chart recommendation engine: 8 recommendations
✓ 11 charts support interactivity (cross-filter + drill-down)
✓ User customization: hide, reorder, change types
✓ Preference persistence: saved to JSON
```

## Future Enhancements

### Phase 3 (Planned - AI-Powered)

- [ ] **LLM-Based Chart Selection**: Use Groq/OpenAI for intelligent chart recommendations
- [ ] **Natural Language Insights**: Auto-generate chart descriptions and findings
- [ ] **Anomaly Detection**: Highlight outliers and unusual patterns
- [ ] **Predictive Analytics**: Add forecasting to time series charts

### Phase 4 (Advanced Features)

- [ ] **Custom Themes**: Dark mode, high contrast, corporate themes
- [ ] **Export Capabilities**: PDF, PNG, interactive HTML export
- [ ] **Real-time Updates**: WebSocket support for live dashboards
- [ ] **Dashboard Templates**: Industry-specific templates (sales, finance, HR)
- [ ] **Collaborative Features**: Comments, annotations, sharing
- [ ] **A/B Testing**: Compare different chart configurations

## Contributing

When adding new chart types:

1. Add chart generation method to `ChartFactory`
2. Update `_generate_charts()` in `DashboardGenerator`
3. Add grid configuration to `LayoutManager._get_chart_grid_config()`
4. Add recommendation rules to `ChartRecommendationEngine` ⭐ NEW
5. Add interactivity config (cross-filter, drill-down) ⭐ NEW
6. Update documentation with examples

## License

Part of the DataCue platform - AI-powered data analysis and visualization system.

---

**Version**: 2.0.0 ⭐ (Phase 2 Complete)
**Last Updated**: 2025  
**Status**: Production Ready ✅

**Phase 2 Features**:

- ✅ Scatter plots with auto-correlation
- ✅ Rule-based chart recommendation engine
- ✅ Cross-filtering & drill-down support
- ✅ Full user customization system
