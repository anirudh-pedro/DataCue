"""
Dashboard Generator Agent
Main orchestrator for automatic dashboard generation
Phase 3: Includes AI insights, advanced charts, performance optimization, and export
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import logging
from .chart_factory import ChartFactory
from .layout_manager import LayoutManager
from .insight_generator import InsightGenerator
from .performance_optimizer import PerformanceOptimizer
from .dashboard_exporter import DashboardExporter

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Generates interactive dashboards from ingested data and metadata
    Uses File Ingestion Agent outputs to create optimized visualizations
    Phase 3: Enhanced with AI insights, advanced charts, and performance optimization
    """
    
    def __init__(self, enable_performance_optimization: bool = True):
        self.chart_factory = ChartFactory()
        self.layout_manager = LayoutManager()
        self.insight_generator = InsightGenerator()
        self.performance_optimizer = PerformanceOptimizer() if enable_performance_optimization else None
        self.exporter = DashboardExporter()
    
    def generate_dashboard(
        self, 
        data: pd.DataFrame, 
        metadata: Dict[str, Any],
        dashboard_type: str = "auto",
        include_advanced_charts: bool = True,
        generate_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete dashboard configuration
        
        Args:
            data: Cleaned DataFrame from File Ingestion Agent
            metadata: Metadata dict with column info, roles, recommendations
            dashboard_type: "auto", "overview", "detailed", "executive"
            include_advanced_charts: Include Phase 3 advanced charts (treemap, funnel, etc.)
            generate_insights: Generate AI-powered insights for all charts
            
        Returns:
            Dictionary with dashboard structure, charts, filters, and config
        """
        try:
            logger.info(f"Generating {dashboard_type} dashboard...")
            
            # Phase 3: Performance optimization
            original_data = data
            optimization_info = {}
            if self.performance_optimizer:
                recommendations = self.performance_optimizer.get_performance_recommendations(data)
                if recommendations:
                    logger.info(f"Performance recommendations: {len(recommendations)} suggestions")
                    optimization_info["recommendations"] = recommendations
            
            # Ensure metadata has required structure
            if 'columns_metadata' not in metadata:
                metadata['columns_metadata'] = {}
                for col in data.columns:
                    metadata['columns_metadata'][col] = {
                        'type': str(data[col].dtype),
                        'suggested_role': 'dimension'
                    }
            
            # Step 1: Analyze metadata and classify columns
            classification = self._classify_columns(metadata)
            
            # Step 2: Generate charts based on recommendations
            charts = self._generate_charts(
                data, 
                metadata, 
                classification,
                include_advanced_charts=include_advanced_charts,
                generate_insights=generate_insights
            )
            
            # Step 3: Create filters and interactivity
            filters = self._generate_filters(metadata, classification)
            
            # Step 4: Build layout
            layout = self.layout_manager.create_layout(
                charts, 
                filters
            )
            
            # Step 5: Add data quality indicators
            quality_indicators = self._create_quality_indicators(metadata)
            
            # Step 6: Create dashboard summary
            summary = self._create_dashboard_summary(metadata, classification)
            
            # Phase 3: Add performance info
            if optimization_info:
                summary["performance"] = optimization_info
            
            dashboard_config = {
                "status": "success",
                "dashboard_id": self._generate_dashboard_id(),
                "title": self._generate_dashboard_title(metadata),
                "summary": summary,
                "layout": layout,
                "charts": charts,
                "filters": filters,
                "quality_indicators": quality_indicators,
                "metadata_summary": {
                    "total_charts": len(charts),
                    "total_filters": len(filters),
                    "data_quality_score": metadata.get('data_quality_score', 0),
                    "dataset_rows": len(original_data),
                    "dataset_columns": len(original_data.columns),
                    "insights_generated": generate_insights,
                    "advanced_charts_enabled": include_advanced_charts
                },
                "version": "3.0.0"  # Phase 3 version
            }
            
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Failed to generate dashboard: {str(e)}"
            }
    
    def _classify_columns(self, metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Classify columns by their roles and characteristics
        """
        classification = {
            "identifiers": [],
            "measures": [],
            "dimensions": [],
            "time_dimensions": [],
            "high_cardinality": [],
            "numeric": [],
            "categorical": []
        }
        
        # Get columns metadata - it's a list, not a dict
        columns_list = metadata.get('columns', [])
        
        for col_meta in columns_list:
            col_name = col_meta.get('name')
            if not col_name:
                continue
                
            # Get role from suggested_role dict
            role_info = col_meta.get('suggested_role', {})
            role = role_info.get('role', 'unknown') if isinstance(role_info, dict) else 'unknown'
            
            col_type = str(col_meta.get('data_type', ''))
            
            # By role
            if role == "identifier":
                classification["identifiers"].append(col_name)
            elif role == "measure":
                classification["measures"].append(col_name)
            elif role in ["dimension", "unknown"]:
                classification["dimensions"].append(col_name)
            elif role == "time_dimension":
                classification["time_dimensions"].append(col_name)
            
            # By type
            if 'int' in col_type or 'float' in col_type:
                classification["numeric"].append(col_name)
            elif 'object' in col_type or 'string' in col_type:
                classification["categorical"].append(col_name)
            
            # High cardinality - it's a dict with is_high_cardinality key
            hc_info = col_meta.get('is_high_cardinality', {})
            if isinstance(hc_info, dict) and hc_info.get('is_high_cardinality', False):
                classification["high_cardinality"].append(col_name)
        
        return classification
    
    def _generate_charts(
        self, 
        data: pd.DataFrame, 
        metadata: Dict[str, Any],
        classification: Dict[str, List[str]],
        include_advanced_charts: bool = True,
        generate_insights: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate all charts for the dashboard
        Phase 3: Includes advanced charts and AI insights
        """
        charts = []
        
        # 1. Overview Charts (KPIs for measures)
        measures_for_kpi = classification["measures"][:5]
        for measure in measures_for_kpi:  # Limit to first 5 measures
            chart = self._create_kpi_card(data, measure, metadata)
            if chart:
                charts.append(chart)
        
        # 2. Distribution Charts (Histograms for numeric)
        numeric_for_hist = classification["numeric"][:4]
        for numeric_col in numeric_for_hist:
            col_meta = self._get_column_metadata(metadata, numeric_col)
            if col_meta and 'histogram' in col_meta.get('chart_recommendations', []):
                chart = self.chart_factory.create_histogram(
                    data, numeric_col, col_meta
                )
                if chart and generate_insights:
                    chart = self._add_insights_to_chart(chart, data)
                if chart:
                    charts.append(chart)
                    logger.info(f"Created histogram for {numeric_col}")
        
        # 3. Categorical Charts (Bar charts for dimensions)
        dims_for_bar = classification["dimensions"][:4]
        logger.info(f"Creating bar charts for dimensions: {dims_for_bar}")
        for dim in dims_for_bar:
            col_meta = self._get_column_metadata(metadata, dim)
            logger.info(f"Dimension {dim} has metadata: {col_meta is not None}")
            if col_meta:
                chart = self.chart_factory.create_bar_chart(
                    data, dim, col_meta
                )
                if chart and generate_insights:
                    chart = self._add_insights_to_chart(chart, data)
                if chart:
                    charts.append(chart)
                    logger.info(f"Created bar chart for {dim}")
        
        # 4. Time Series Charts
        if classification["time_dimensions"]:
            time_col = classification["time_dimensions"][0]
            for measure in classification["measures"][:2]:
                chart = self.chart_factory.create_time_series(
                    data, time_col, measure
                )
                if chart and generate_insights:
                    chart = self._add_insights_to_chart(chart, data)
                if chart:
                    charts.append(chart)
        
        # 5. Scatter Plots (Numeric vs Numeric)
        numeric_cols = classification["numeric"]
        if len(numeric_cols) >= 2:
            # Create scatter plots for top numeric column pairs
            for i in range(min(2, len(numeric_cols) - 1)):
                chart = self.chart_factory.create_scatter_plot(
                    data, numeric_cols[i], numeric_cols[i + 1]
                )
                if chart and generate_insights:
                    chart = self._add_insights_to_chart(chart, data)
                if chart:
                    charts.append(chart)
        
        # 6. Correlation Heatmap
        if metadata.get('correlation_matrix', {}).get('available'):
            chart = self.chart_factory.create_correlation_heatmap(
                data, metadata['correlation_matrix']
            )
            if chart:
                charts.append(chart)
        
        # 7. Measure vs Dimension Charts
        if classification["measures"] and classification["dimensions"]:
            # Create a few combo charts
            for i, measure in enumerate(classification["measures"][:2]):
                if i < len(classification["dimensions"]):
                    dim = classification["dimensions"][i]
                    chart = self.chart_factory.create_grouped_bar(
                        data, dim, measure
                    )
                    if chart and generate_insights:
                        chart = self._add_insights_to_chart(chart, data)
                    if chart:
                        charts.append(chart)
        
        # Phase 3: Advanced Charts
        if include_advanced_charts:
            advanced_charts = self._generate_advanced_charts(
                data, 
                classification,
                generate_insights
            )
            charts.extend(advanced_charts)
        
        return charts
    
    def _generate_advanced_charts(
        self,
        data: pd.DataFrame,
        classification: Dict[str, List[str]],
        generate_insights: bool
    ) -> List[Dict[str, Any]]:
        """
        Generate Phase 3 advanced charts (treemap, funnel, sankey, stacked area)
        """
        advanced_charts = []
        
        try:
            # 1. Treemap - hierarchical data visualization
            if classification["dimensions"] and classification["measures"]:
                # Use first dimension and measure for treemap
                dim = classification["dimensions"][0]
                measure = classification["measures"][0] if classification["measures"] else None
                
                if measure:
                    chart = self.chart_factory.create_treemap(
                        data, dim, measure
                    )
                    if chart and generate_insights:
                        chart = self._add_insights_to_chart(chart, data)
                    if chart:
                        advanced_charts.append(chart)
            
            # 2. Funnel - conversion analysis
            # Create funnel if we have categorical column with sequential data
            if len(classification["dimensions"]) > 0 and len(classification["measures"]) > 0:
                stage_col = classification["dimensions"][0]
                value_col = classification["measures"][0]
                
                # Check if suitable for funnel (limited categories)
                if data[stage_col].nunique() <= 10:
                    chart = self.chart_factory.create_funnel(
                        data, stage_col, value_col
                    )
                    if chart and generate_insights:
                        chart = self._add_insights_to_chart(chart, data)
                    if chart:
                        advanced_charts.append(chart)
            
            # 3. Sankey - flow diagram
            # Create sankey if we have at least 2 categorical columns
            if len(classification["dimensions"]) >= 2:
                source_col = classification["dimensions"][0]
                target_col = classification["dimensions"][1]
                value_col = classification["measures"][0] if classification["measures"] else None
                
                chart = self.chart_factory.create_sankey(
                    data, source_col, target_col, value_col
                )
                if chart and generate_insights:
                    chart = self._add_insights_to_chart(chart, data)
                if chart:
                    advanced_charts.append(chart)
            
            # 4. Stacked Area - time series composition
            if classification["time_dimensions"] and classification["dimensions"]:
                time_col = classification["time_dimensions"][0]
                category_col = classification["dimensions"][0]
                value_col = classification["measures"][0] if classification["measures"] else None
                
                if value_col:
                    chart = self.chart_factory.create_stacked_area(
                        data, time_col, value_col, category_col
                    )
                    if chart and generate_insights:
                        chart = self._add_insights_to_chart(chart, data)
                    if chart:
                        advanced_charts.append(chart)
        
        except Exception as e:
            logger.warning(f"Error generating advanced charts: {str(e)}")
        
        return advanced_charts
    
    def _add_insights_to_chart(
        self,
        chart: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Add AI-generated insights to a chart
        """
        try:
            chart_type = chart.get('type')
            columns = chart.get('columns', {})
            
            # Generate insights based on chart type
            insights = self.insight_generator.generate_insight(
                data=data,
                chart_type=chart_type,
                columns=columns
            )
            
            if insights:
                chart['ai_insights'] = insights
                logger.info(f"Generated insights for chart {chart.get('id')}")
        
        except Exception as e:
            logger.warning(f"Error generating insights for chart: {str(e)}")
        
        return chart
    
    def _create_kpi_card(
        self, 
        data: pd.DataFrame, 
        measure: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a KPI card for a measure
        """
        try:
            col_meta = self._get_column_metadata(metadata, measure)
            if not col_meta:
                return None
            
            value = data[measure].sum()
            avg = data[measure].mean()
            max_val = data[measure].max()
            min_val = data[measure].min()
            
            return {
                "id": f"kpi_{measure}",
                "type": "kpi",
                "title": f"{measure.replace('_', ' ').title()}",
                "data": {
                    "primary_value": float(value),
                    "average": float(avg),
                    "max": float(max_val),
                    "min": float(min_val)
                },
                "config": {
                    "format": "number",
                    "precision": 2
                }
            }
        except Exception as e:
            logger.warning(f"Error creating KPI for {measure}: {str(e)}")
            return None
    
    def _generate_filters(
        self, 
        metadata: Dict[str, Any],
        classification: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate interactive filters for the dashboard
        """
        filters = []
        
        # Dimension filters (dropdowns)
        for dim in classification["dimensions"][:5]:  # Limit to 5 filters
            col_meta = self._get_column_metadata(metadata, dim)
            if col_meta and col_meta['unique_count'] < 50:  # Only if manageable
                filters.append({
                    "id": f"filter_{dim}",
                    "type": "dropdown",
                    "column": dim,
                    "label": dim.replace('_', ' ').title(),
                    "multi_select": True,
                    "default": "all"
                })
        
        # Time range filter
        if classification["time_dimensions"]:
            time_col = classification["time_dimensions"][0]
            filters.append({
                "id": f"filter_{time_col}",
                "type": "date_range",
                "column": time_col,
                "label": "Date Range",
                "default": "all"
            })
        
        # Numeric range filters
        for numeric in classification["numeric"][:2]:
            if numeric in classification["measures"]:
                col_meta = self._get_column_metadata(metadata, numeric)
                if col_meta:
                    filters.append({
                        "id": f"filter_{numeric}",
                        "type": "range_slider",
                        "column": numeric,
                        "label": numeric.replace('_', ' ').title(),
                        "min": col_meta.get('min', 0),
                        "max": col_meta.get('max', 100),
                        "default": [col_meta.get('min', 0), col_meta.get('max', 100)]
                    })
        
        return filters
    
    def _create_quality_indicators(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create data quality indicators for dashboard
        """
        quality_score = metadata.get('data_quality_score', 0)
        quality_components = metadata.get('quality_components', {})
        
        return {
            "overall_score": quality_score,
            "rating": "excellent" if quality_score >= 90 else "good" if quality_score >= 70 else "fair" if quality_score >= 50 else "poor",
            "components": quality_components,
            "issues": [],
            "show_warning": quality_score < 70
        }
    
    def _create_dashboard_summary(
        self, 
        metadata: Dict[str, Any],
        classification: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Create dashboard summary information
        """
        insights = metadata.get('insights', [])
        quality_score = metadata.get('data_quality_score', 0)
        
        return {
            "dataset_insights": insights if isinstance(insights, list) else [],
            "key_metrics": classification["measures"][:5],
            "key_dimensions": classification["dimensions"][:5],
            "time_columns": classification["time_dimensions"],
            "data_quality": "excellent" if quality_score >= 90 else "good" if quality_score >= 70 else "fair" if quality_score >= 50 else "poor"
        }
    
    def _get_column_metadata(self, metadata: Dict[str, Any], col_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific column (searches columns list)
        """
        columns_list = metadata.get('columns', [])
        for col_meta in columns_list:
            if col_meta.get('name') == col_name:
                return col_meta
        return None
    
    def _generate_dashboard_id(self) -> str:
        """
        Generate unique dashboard ID
        """
        import uuid
        return f"dashboard_{uuid.uuid4().hex[:8]}"
    
    def _generate_dashboard_title(self, metadata: Dict[str, Any]) -> str:
        """
        Generate descriptive dashboard title
        """
        insights = metadata.get('advanced_insights', {})
        characteristics = insights.get('data_characteristics', [])
        
        if characteristics:
            return f"Dashboard - {characteristics[0]}"
        return "Data Analysis Dashboard"
    
    # Phase 3: Export Methods
    
    def export_dashboard(
        self,
        dashboard_config: Dict[str, Any],
        format: str = "json",
        **export_options
    ) -> str:
        """
        Export dashboard to various formats
        
        Args:
            dashboard_config: Complete dashboard configuration
            format: Export format ("json", "pdf", "png", "html")
            **export_options: Format-specific options
            
        Returns:
            Path to exported file
        """
        if format == "json":
            return self.exporter.save_dashboard_config(
                dashboard_config,
                export_options.get('filename')
            )
        elif format == "pdf":
            return self.exporter.export_to_pdf(
                dashboard_config,
                export_options.get('filename'),
                export_options.get('include_insights', True)
            )
        elif format == "png":
            return self.exporter.export_to_png(
                dashboard_config,
                export_options.get('chart_id'),
                export_options.get('width', 1200),
                export_options.get('height', 800)
            )
        elif format == "html":
            return self.exporter.export_to_html(
                dashboard_config,
                export_options.get('filename'),
                export_options.get('standalone', True)
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_export_capabilities(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get export capabilities and file size estimates
        
        Args:
            dashboard_config: Dashboard configuration
            
        Returns:
            Export summary with capabilities and estimates
        """
        return self.exporter.get_export_summary(dashboard_config)
