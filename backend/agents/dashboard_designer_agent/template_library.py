"""
Dashboard Designer Agent - Template Library
Predefined dashboard templates with section definitions
"""
from models.dashboard_models import (
    DashboardTemplate,
    TemplateSection,
    SectionType,
    ChartType
)
from typing import List, Dict


class TemplateLibrary:
    """Library of predefined dashboard templates"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, DashboardTemplate]:
        """Initialize all predefined templates"""
        return {
            "sales_overview": self._create_sales_template(),
            "data_analytics": self._create_analytics_template(),
            "executive_summary": self._create_executive_template(),
            "customer_insights": self._create_customer_template(),
            "performance_metrics": self._create_performance_template()
        }
    
    def _create_sales_template(self) -> DashboardTemplate:
        """Sales Overview Template"""
        return DashboardTemplate(
            template_id="sales_overview",
            name="Sales Overview",
            description="Comprehensive sales performance dashboard with revenue, trends, and product analysis",
            category="Sales",
            icon="💰",
            layout_type="grid",
            color_scheme="blue",
            sections=[
                TemplateSection(
                    section_id="header",
                    section_type=SectionType.HEADER,
                    title="Dashboard Title",
                    description="Main dashboard header with title and date range",
                    position=0,
                    size="full",
                    required=True
                ),
                TemplateSection(
                    section_id="total_revenue",
                    section_type=SectionType.KPI,
                    title="Total Revenue",
                    description="Sum of all revenue",
                    position=1,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="total_orders",
                    section_type=SectionType.KPI,
                    title="Total Orders",
                    description="Count of all orders",
                    position=2,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="avg_order_value",
                    section_type=SectionType.KPI,
                    title="Avg Order Value",
                    description="Average revenue per order",
                    position=3,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="revenue_trend",
                    section_type=SectionType.CHART,
                    title="Revenue Over Time",
                    description="Time series of revenue trends",
                    position=4,
                    size="large",
                    required=True,
                    default_chart_type=ChartType.LINE,
                    allowed_chart_types=[ChartType.LINE, ChartType.AREA, ChartType.BAR]
                ),
                TemplateSection(
                    section_id="top_products",
                    section_type=SectionType.CHART,
                    title="Top Products by Revenue",
                    description="Bar chart showing best-selling products",
                    position=5,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.BAR,
                    allowed_chart_types=[ChartType.BAR, ChartType.PIE, ChartType.TREEMAP]
                ),
                TemplateSection(
                    section_id="category_distribution",
                    section_type=SectionType.CHART,
                    title="Sales by Category",
                    description="Distribution of sales across product categories",
                    position=6,
                    size="medium",
                    required=False,
                    default_chart_type=ChartType.PIE,
                    allowed_chart_types=[ChartType.PIE, ChartType.BAR, ChartType.TREEMAP]
                )
            ]
        )
    
    def _create_analytics_template(self) -> DashboardTemplate:
        """Data Analytics Template"""
        return DashboardTemplate(
            template_id="data_analytics",
            name="Data Analytics",
            description="General-purpose analytics dashboard for exploring data patterns and distributions",
            category="Analytics",
            icon="📊",
            layout_type="grid",
            color_scheme="purple",
            sections=[
                TemplateSection(
                    section_id="header",
                    section_type=SectionType.HEADER,
                    title="Analytics Dashboard",
                    description="Data analysis and insights",
                    position=0,
                    size="full",
                    required=True
                ),
                TemplateSection(
                    section_id="key_metric_1",
                    section_type=SectionType.KPI,
                    title="Primary Metric",
                    description="Main KPI to track",
                    position=1,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="key_metric_2",
                    section_type=SectionType.KPI,
                    title="Secondary Metric",
                    description="Supporting KPI",
                    position=2,
                    size="small",
                    required=False
                ),
                TemplateSection(
                    section_id="trend_analysis",
                    section_type=SectionType.CHART,
                    title="Trend Analysis",
                    description="Time-based trends in your data",
                    position=3,
                    size="large",
                    required=True,
                    default_chart_type=ChartType.LINE,
                    allowed_chart_types=[ChartType.LINE, ChartType.AREA, ChartType.BAR, ChartType.SCATTER]
                ),
                TemplateSection(
                    section_id="distribution",
                    section_type=SectionType.CHART,
                    title="Data Distribution",
                    description="Distribution of key variables",
                    position=4,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.HISTOGRAM,
                    allowed_chart_types=[ChartType.HISTOGRAM, ChartType.BOX, ChartType.BAR]
                ),
                TemplateSection(
                    section_id="comparison",
                    section_type=SectionType.CHART,
                    title="Category Comparison",
                    description="Compare values across categories",
                    position=5,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.BAR,
                    allowed_chart_types=[ChartType.BAR, ChartType.PIE, ChartType.TREEMAP]
                ),
                TemplateSection(
                    section_id="correlation",
                    section_type=SectionType.CHART,
                    title="Correlation Analysis",
                    description="Relationship between variables",
                    position=6,
                    size="medium",
                    required=False,
                    default_chart_type=ChartType.SCATTER,
                    allowed_chart_types=[ChartType.SCATTER, ChartType.HEATMAP]
                )
            ]
        )
    
    def _create_executive_template(self) -> DashboardTemplate:
        """Executive Summary Template"""
        return DashboardTemplate(
            template_id="executive_summary",
            name="Executive Summary",
            description="High-level overview dashboard for executives with key metrics and insights",
            category="Executive",
            icon="👔",
            layout_type="grid",
            color_scheme="green",
            sections=[
                TemplateSection(
                    section_id="header",
                    section_type=SectionType.HEADER,
                    title="Executive Summary",
                    description="Key performance indicators at a glance",
                    position=0,
                    size="full",
                    required=True
                ),
                TemplateSection(
                    section_id="kpi_1",
                    section_type=SectionType.KPI,
                    title="KPI 1",
                    description="Primary business metric",
                    position=1,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="kpi_2",
                    section_type=SectionType.KPI,
                    title="KPI 2",
                    description="Secondary business metric",
                    position=2,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="kpi_3",
                    section_type=SectionType.KPI,
                    title="KPI 3",
                    description="Tertiary business metric",
                    position=3,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="kpi_4",
                    section_type=SectionType.KPI,
                    title="KPI 4",
                    description="Additional metric",
                    position=4,
                    size="small",
                    required=False
                ),
                TemplateSection(
                    section_id="performance_overview",
                    section_type=SectionType.CHART,
                    title="Performance Overview",
                    description="Overall business performance trends",
                    position=5,
                    size="large",
                    required=True,
                    default_chart_type=ChartType.LINE,
                    allowed_chart_types=[ChartType.LINE, ChartType.AREA, ChartType.BAR]
                ),
                TemplateSection(
                    section_id="breakdown",
                    section_type=SectionType.CHART,
                    title="Performance Breakdown",
                    description="Detailed breakdown by segment",
                    position=6,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.BAR,
                    allowed_chart_types=[ChartType.BAR, ChartType.PIE, ChartType.TREEMAP]
                )
            ]
        )
    
    def _create_customer_template(self) -> DashboardTemplate:
        """Customer Insights Template"""
        return DashboardTemplate(
            template_id="customer_insights",
            name="Customer Insights",
            description="Customer behavior and segmentation analysis dashboard",
            category="Customer",
            icon="👥",
            layout_type="grid",
            color_scheme="orange",
            sections=[
                TemplateSection(
                    section_id="header",
                    section_type=SectionType.HEADER,
                    title="Customer Insights",
                    description="Understand your customer base",
                    position=0,
                    size="full",
                    required=True
                ),
                TemplateSection(
                    section_id="total_customers",
                    section_type=SectionType.KPI,
                    title="Total Customers",
                    description="Count of unique customers",
                    position=1,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="customer_lifetime_value",
                    section_type=SectionType.KPI,
                    title="Avg Customer Value",
                    description="Average lifetime value per customer",
                    position=2,
                    size="small",
                    required=False
                ),
                TemplateSection(
                    section_id="customer_growth",
                    section_type=SectionType.CHART,
                    title="Customer Growth",
                    description="Customer acquisition over time",
                    position=3,
                    size="large",
                    required=True,
                    default_chart_type=ChartType.LINE,
                    allowed_chart_types=[ChartType.LINE, ChartType.AREA, ChartType.BAR]
                ),
                TemplateSection(
                    section_id="customer_segments",
                    section_type=SectionType.CHART,
                    title="Customer Segments",
                    description="Distribution of customer segments",
                    position=4,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.PIE,
                    allowed_chart_types=[ChartType.PIE, ChartType.BAR, ChartType.TREEMAP]
                ),
                TemplateSection(
                    section_id="customer_behavior",
                    section_type=SectionType.CHART,
                    title="Customer Behavior",
                    description="Purchase patterns and behavior analysis",
                    position=5,
                    size="medium",
                    required=False,
                    default_chart_type=ChartType.BAR,
                    allowed_chart_types=[ChartType.BAR, ChartType.SCATTER, ChartType.HEATMAP]
                )
            ]
        )
    
    def _create_performance_template(self) -> DashboardTemplate:
        """Performance Metrics Template"""
        return DashboardTemplate(
            template_id="performance_metrics",
            name="Performance Metrics",
            description="Track and monitor performance metrics and KPIs",
            category="Performance",
            icon="📈",
            layout_type="grid",
            color_scheme="red",
            sections=[
                TemplateSection(
                    section_id="header",
                    section_type=SectionType.HEADER,
                    title="Performance Metrics",
                    description="Monitor key performance indicators",
                    position=0,
                    size="full",
                    required=True
                ),
                TemplateSection(
                    section_id="metric_1",
                    section_type=SectionType.KPI,
                    title="Metric 1",
                    description="Primary performance metric",
                    position=1,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="metric_2",
                    section_type=SectionType.KPI,
                    title="Metric 2",
                    description="Secondary performance metric",
                    position=2,
                    size="small",
                    required=True
                ),
                TemplateSection(
                    section_id="metric_3",
                    section_type=SectionType.KPI,
                    title="Metric 3",
                    description="Tertiary performance metric",
                    position=3,
                    size="small",
                    required=False
                ),
                TemplateSection(
                    section_id="performance_trends",
                    section_type=SectionType.CHART,
                    title="Performance Trends",
                    description="Track metrics over time",
                    position=4,
                    size="large",
                    required=True,
                    default_chart_type=ChartType.LINE,
                    allowed_chart_types=[ChartType.LINE, ChartType.AREA, ChartType.BAR]
                ),
                TemplateSection(
                    section_id="metric_comparison",
                    section_type=SectionType.CHART,
                    title="Metric Comparison",
                    description="Compare different metrics or segments",
                    position=5,
                    size="medium",
                    required=True,
                    default_chart_type=ChartType.BAR,
                    allowed_chart_types=[ChartType.BAR, ChartType.SCATTER, ChartType.BOX]
                ),
                TemplateSection(
                    section_id="performance_distribution",
                    section_type=SectionType.CHART,
                    title="Performance Distribution",
                    description="Distribution of performance metrics",
                    position=6,
                    size="medium",
                    required=False,
                    default_chart_type=ChartType.HISTOGRAM,
                    allowed_chart_types=[ChartType.HISTOGRAM, ChartType.BOX, ChartType.BAR]
                )
            ]
        )
    
    def get_template(self, template_id: str) -> DashboardTemplate:
        """Get template by ID"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        return template
    
    def list_templates(self) -> List[DashboardTemplate]:
        """Get all available templates"""
        return list(self.templates.values())
    
    def get_templates_by_category(self, category: str) -> List[DashboardTemplate]:
        """Get templates filtered by category"""
        return [t for t in self.templates.values() if t.category.lower() == category.lower()]
