"""
Layout Manager
Manages dashboard layout and responsive chart arrangement
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class LayoutManager:
    """
    Manages dashboard layout, chart positioning, and responsive design
    """
    
    def __init__(self):
        self.grid_columns = 12  # Bootstrap-style grid
        self.breakpoints = {
            'xs': 0,
            'sm': 576,
            'md': 768,
            'lg': 992,
            'xl': 1200,
            'xxl': 1400
        }
    
    def create_layout(
        self,
        charts: List[Dict[str, Any]],
        filters: List[Dict[str, Any]],
        kpis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create complete dashboard layout configuration
        
        Returns layout structure for frontend rendering:
        {
            "grid": {...},
            "sections": [...],
            "responsive_config": {...}
        }
        """
        sections = []
        
        # Section 1: KPIs (if available)
        if kpis:
            sections.append(self._create_kpi_section(kpis))
        
        # Section 2: Filters sidebar
        if filters:
            sections.append(self._create_filter_section(filters))
        
        # Section 3: Charts grid
        sections.append(self._create_charts_section(charts))
        
        return {
            "grid_columns": self.grid_columns,
            "sections": sections,
            "responsive_config": self._get_responsive_config(),
            "layout_type": "dashboard",
            "has_sidebar": len(filters) > 0,
            "has_kpis": kpis is not None and len(kpis) > 0
        }
    
    def _create_kpi_section(self, kpis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create KPI section layout (top of dashboard)
        """
        kpi_items = []
        
        # Distribute KPIs evenly
        kpi_count = len(kpis)
        columns_per_kpi = self.grid_columns // min(kpi_count, 4)  # Max 4 KPIs per row
        
        for idx, kpi in enumerate(kpis):
            kpi_items.append({
                "id": kpi.get('id', f"kpi_{idx}"),
                "type": "kpi",
                "title": kpi.get('title', ''),
                "value": kpi.get('value'),
                "change": kpi.get('change'),
                "grid": {
                    "xs": 12,  # Full width on mobile
                    "sm": 6,   # Half width on small screens
                    "md": columns_per_kpi,  # Calculated width
                    "lg": columns_per_kpi,
                    "xl": columns_per_kpi
                },
                "order": idx
            })
        
        return {
            "id": "kpi_section",
            "type": "kpi_row",
            "title": "Key Metrics",
            "items": kpi_items,
            "grid": {
                "xs": 12,
                "sm": 12,
                "md": 12,
                "lg": 12,
                "xl": 12
            },
            "order": 0
        }
    
    def _create_filter_section(self, filters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create filters sidebar section
        """
        filter_items = []
        
        for idx, filter_item in enumerate(filters):
            filter_items.append({
                "id": filter_item.get('id', f"filter_{idx}"),
                "type": filter_item.get('type', 'select'),
                "label": filter_item.get('label', ''),
                "column": filter_item.get('column', ''),
                "options": filter_item.get('options', []),
                "config": filter_item.get('config', {}),
                "order": idx
            })
        
        return {
            "id": "filter_section",
            "type": "sidebar",
            "title": "Filters",
            "items": filter_items,
            "grid": {
                "xs": 12,  # Full width on mobile (top)
                "sm": 12,
                "md": 3,   # Sidebar on medium+
                "lg": 3,
                "xl": 2
            },
            "order": 1,
            "position": "left"
        }
    
    def _create_charts_section(self, charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create charts grid section with intelligent positioning
        """
        chart_items = []
        
        for idx, chart in enumerate(charts):
            chart_type = chart.get('type', 'unknown')
            grid_config = self._get_chart_grid_config(chart_type, idx, len(charts))
            
            chart_items.append({
                "id": chart.get('id', f"chart_{idx}"),
                "type": chart_type,
                "title": chart.get('title', ''),
                "column": chart.get('column', ''),
                "grid": grid_config,
                "order": idx,
                "height": self._get_chart_height(chart_type)
            })
        
        return {
            "id": "charts_section",
            "type": "grid",
            "title": "Visualizations",
            "items": chart_items,
            "grid": {
                "xs": 12,
                "sm": 12,
                "md": 9,   # Main area (when sidebar present)
                "lg": 9,
                "xl": 10
            },
            "order": 2
        }
    
    def _get_chart_grid_config(
        self, 
        chart_type: str,
        index: int,
        total_charts: int
    ) -> Dict[str, int]:
        """
        Get responsive grid configuration for a specific chart type
        """
        # Default: Half width on medium screens, full width on small
        default_config = {
            "xs": 12,
            "sm": 12,
            "md": 6,
            "lg": 6,
            "xl": 6
        }
        
        # Special configurations by chart type
        if chart_type in ['correlation_heatmap', 'time_series']:
            # Wide charts get full width
            return {
                "xs": 12,
                "sm": 12,
                "md": 12,
                "lg": 12,
                "xl": 12
            }
        
        elif chart_type in ['pie', 'kpi']:
            # Smaller charts can fit 3 per row on large screens
            return {
                "xs": 12,
                "sm": 6,
                "md": 4,
                "lg": 4,
                "xl": 4
            }
        
        elif chart_type in ['histogram', 'box_plot']:
            # Medium charts, 2 per row
            return {
                "xs": 12,
                "sm": 12,
                "md": 6,
                "lg": 6,
                "xl": 6
            }
        
        else:
            return default_config
    
    def _get_chart_height(self, chart_type: str) -> int:
        """
        Get recommended height (in pixels) for chart type
        """
        height_map = {
            'kpi': 120,
            'pie': 350,
            'histogram': 400,
            'bar': 400,
            'box_plot': 400,
            'time_series': 450,
            'correlation_heatmap': 500,
            'grouped_bar': 450,
            'scatter': 400
        }
        
        return height_map.get(chart_type, 400)
    
    def _get_responsive_config(self) -> Dict[str, Any]:
        """
        Get responsive behavior configuration
        """
        return {
            "breakpoints": self.breakpoints,
            "mobile_behavior": {
                "stack_charts": True,
                "collapse_sidebar": True,
                "hide_legends": False
            },
            "tablet_behavior": {
                "stack_charts": False,
                "collapse_sidebar": False,
                "hide_legends": False
            },
            "desktop_behavior": {
                "stack_charts": False,
                "collapse_sidebar": False,
                "hide_legends": False
            }
        }
    
    def get_export_config(self, charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get configuration for dashboard export (PDF, image, etc.)
        """
        return {
            "page_size": "A4",
            "orientation": "landscape",
            "charts_per_page": 4,
            "include_filters": True,
            "include_kpis": True,
            "total_charts": len(charts),
            "estimated_pages": (len(charts) + 3) // 4  # Round up
        }
    
    def optimize_layout(
        self,
        charts: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Optimize chart order and grouping for better UX
        
        Grouping logic:
        1. KPIs at top
        2. Time series charts (important trends)
        3. Distribution charts (histograms, box plots)
        4. Category charts (bar, pie)
        5. Correlation heatmap (advanced analysis)
        """
        preferences = preferences or {}
        
        priority_order = {
            'kpi': 0,
            'time_series': 1,
            'histogram': 2,
            'box_plot': 3,
            'bar': 4,
            'grouped_bar': 5,
            'pie': 6,
            'scatter': 7,
            'correlation_heatmap': 8
        }
        
        # Sort charts by type priority
        sorted_charts = sorted(
            charts,
            key=lambda c: priority_order.get(c.get('type', 'unknown'), 99)
        )
        
        return sorted_charts
