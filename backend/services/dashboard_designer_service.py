"""
Dashboard Designer Service
Business logic for template-based dashboard generation
"""
import pandas as pd
import uuid
from typing import List, Dict, Optional
from datetime import datetime

from models.dashboard_models import (
    DashboardTemplate,
    DashboardConfig,
    ChartOption,
    ChartOptionsResponse,
    DatasetInfo,
    TemplateSection,
    GenerateDashboardResponse
)
from agents.dashboard_designer_agent import (
    TemplateLibrary,
    DataAnalyzer,
    DashboardDesignerAgent
)
from shared import storage


class DashboardDesignerService:
    """Service layer for dashboard designer functionality"""
    
    def __init__(self):
        self.template_library = TemplateLibrary()
        self.data_analyzer = DataAnalyzer()
        self._designer_agent = None  # Lazy initialization
    
    @property
    def designer_agent(self):
        """Lazy initialization of designer agent (requires API key)"""
        if self._designer_agent is None:
            self._designer_agent = DashboardDesignerAgent()
        return self._designer_agent
    
    def get_all_templates(self) -> List[DashboardTemplate]:
        """
        Get all available dashboard templates
        
        Returns:
            List of DashboardTemplate objects
        """
        return self.template_library.list_templates()
    
    def get_template_by_id(self, template_id: str) -> DashboardTemplate:
        """
        Get a specific template by ID
        
        Args:
            template_id: Template identifier
            
        Returns:
            DashboardTemplate object
            
        Raises:
            ValueError: If template not found
        """
        return self.template_library.get_template(template_id)
    
    def get_chart_options(
        self, 
        dataset_id: str, 
        section_id: str,
        template_id: str
    ) -> ChartOptionsResponse:
        """
        Get available chart options for a specific section
        
        Args:
            dataset_id: Dataset identifier
            section_id: Section identifier
            template_id: Template identifier
            
        Returns:
            ChartOptionsResponse with available options
        """
        # Load dataset
        df = self._load_dataset(dataset_id)
        
        # Analyze dataset
        dataset_info = self.data_analyzer.analyze_dataset(df, dataset_id)
        
        # Get template and section
        template = self.template_library.get_template(template_id)
        section = next((s for s in template.sections if s.section_id == section_id), None)
        
        if not section:
            raise ValueError(f"Section '{section_id}' not found in template '{template_id}'")
        
        # Get available chart types for this section
        available_chart_types = section.allowed_chart_types
        if not available_chart_types and section.default_chart_type:
            available_chart_types = [section.default_chart_type]
        
        # If a default chart type exists, get options for it
        if section.default_chart_type:
            x_options, y_options, color_options = self.data_analyzer.get_axis_options(
                dataset_info, 
                section.default_chart_type
            )
        else:
            # Get options for first allowed chart type
            x_options, y_options, color_options = self.data_analyzer.get_axis_options(
                dataset_info,
                available_chart_types[0] if available_chart_types else None
            )
        
        return ChartOptionsResponse(
            section_id=section_id,
            available_chart_types=available_chart_types,
            x_axis_options=x_options,
            y_axis_options=y_options,
            color_options=color_options,
            aggregation_options=self.data_analyzer.get_aggregation_functions(
                section.default_chart_type or available_chart_types[0]
            )
        )
    
    def set_section_config(
        self,
        dataset_id: str,
        template_id: str,
        section_id: str,
        chart_config: ChartOption,
        dashboard_id: Optional[str] = None
    ) -> DashboardConfig:
        """
        Configure a specific section in a dashboard
        
        Args:
            dataset_id: Dataset identifier
            template_id: Template identifier
            section_id: Section identifier
            chart_config: Chart configuration
            dashboard_id: Optional existing dashboard ID
            
        Returns:
            Updated DashboardConfig
        """
        # Load dataset for validation
        df = self._load_dataset(dataset_id)
        dataset_info = self.data_analyzer.analyze_dataset(df, dataset_id)
        
        # Validate chart configuration
        is_valid, error_msg = self.data_analyzer.validate_chart_config(
            dataset_info,
            chart_config.chart_type,
            chart_config.x_axis,
            chart_config.y_axis,
            chart_config.color_by
        )
        
        if not is_valid:
            raise ValueError(f"Invalid chart configuration: {error_msg}")
        
        # Load or create dashboard config
        if dashboard_id:
            dashboard_config = self._load_dashboard_config(dashboard_id)
        else:
            # Create new dashboard from template
            template = self.template_library.get_template(template_id)
            dashboard_id = str(uuid.uuid4())
            
            dashboard_config = DashboardConfig(
                dashboard_id=dashboard_id,
                template_id=template_id,
                dataset_id=dataset_id,
                title=template.name,
                description=template.description,
                sections=template.sections.copy(),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
        
        # Update the specific section
        for section in dashboard_config.sections:
            if section.section_id == section_id:
                section.chart_config = chart_config
                break
        else:
            raise ValueError(f"Section '{section_id}' not found in dashboard")
        
        # Update timestamp
        dashboard_config.updated_at = datetime.utcnow().isoformat()
        
        # Save dashboard config
        self._save_dashboard_config(dashboard_config)
        
        return dashboard_config
    
    def generate_dashboard(
        self,
        dataset_id: str,
        user_prompt: Optional[str] = None
    ) -> GenerateDashboardResponse:
        """
        Generate a complete dashboard using AI
        
        Args:
            dataset_id: Dataset identifier
            user_prompt: Optional user guidance
            
        Returns:
            GenerateDashboardResponse with config and AI reasoning
        """
        # Load dataset
        df = self._load_dataset(dataset_id)
        
        # Generate dashboard using AI
        dashboard_config, reasoning = self.designer_agent.generate_dashboard(
            df, 
            dataset_id, 
            user_prompt
        )
        
        # Add timestamps
        dashboard_config.created_at = datetime.utcnow().isoformat()
        dashboard_config.updated_at = datetime.utcnow().isoformat()
        
        # Save dashboard config
        self._save_dashboard_config(dashboard_config)
        
        return GenerateDashboardResponse(
            dashboard_id=dashboard_config.dashboard_id,
            config=dashboard_config,
            ai_reasoning=reasoning
        )
    
    def finalize_dashboard(
        self,
        dashboard_id: str
    ) -> Dict:
        """
        Finalize a dashboard and generate all charts
        
        Args:
            dashboard_id: Dashboard identifier
            
        Returns:
            Dictionary with dashboard data and charts
        """
        # Load dashboard config
        dashboard_config = self._load_dashboard_config(dashboard_id)
        
        # Load dataset
        df = self._load_dataset(dashboard_config.dataset_id)
        
        # Generate charts for each section
        charts = []
        kpis = []
        
        for section in dashboard_config.sections:
            if section.section_type.value == "kpi":
                # Calculate KPI value
                kpi_value = self._calculate_kpi(df, section)
                kpis.append({
                    "section_id": section.section_id,
                    "title": section.title,
                    "value": kpi_value,
                    "description": section.description
                })
            
            elif section.section_type.value == "chart" and section.chart_config:
                # Generate chart data
                chart_data = self._generate_chart_data(df, section)
                charts.append(chart_data)
        
        return {
            "dashboard_id": dashboard_id,
            "title": dashboard_config.title,
            "description": dashboard_config.description,
            "kpis": kpis,
            "charts": charts,
            "created_at": dashboard_config.created_at,
            "updated_at": dashboard_config.updated_at
        }
    
    def _load_dataset(self, dataset_id: str) -> pd.DataFrame:
        """Load dataset from storage"""
        metadata = storage.load_metadata(dataset_id)
        if not metadata:
            raise ValueError(f"Dataset '{dataset_id}' not found")
        
        file_path = metadata.get('file_path')
        df = pd.read_csv(file_path)
        return df
    
    def _save_dashboard_config(self, config: DashboardConfig):
        """Save dashboard configuration to storage"""
        # Convert to dict and save as metadata
        config_dict = config.model_dump()
        storage.save_metadata(f"dashboard_{config.dashboard_id}", config_dict)
    
    def _load_dashboard_config(self, dashboard_id: str) -> DashboardConfig:
        """Load dashboard configuration from storage"""
        config_dict = storage.load_metadata(f"dashboard_{dashboard_id}")
        if not config_dict:
            raise ValueError(f"Dashboard '{dashboard_id}' not found")
        
        return DashboardConfig(**config_dict)
    
    def _calculate_kpi(self, df: pd.DataFrame, section: TemplateSection) -> float:
        """Calculate KPI value for a section"""
        # Simple logic: try to infer from title what to calculate
        title_lower = section.title.lower()
        
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return len(df)  # Return count if no numeric columns
        
        # Try to match column name from title
        for col in numeric_cols:
            if col.lower() in title_lower or any(word in col.lower() for word in title_lower.split()):
                if 'total' in title_lower or 'sum' in title_lower:
                    return float(df[col].sum())
                elif 'avg' in title_lower or 'average' in title_lower:
                    return float(df[col].mean())
                elif 'count' in title_lower:
                    return float(df[col].count())
                else:
                    return float(df[col].sum())  # Default to sum
        
        # Default: sum of first numeric column
        return float(df[numeric_cols[0]].sum())
    
    def _generate_chart_data(self, df: pd.DataFrame, section: TemplateSection) -> Dict:
        """Generate chart data for a section"""
        config = section.chart_config
        
        if not config:
            return {}
        
        # Prepare data based on chart type and configuration
        chart_data = {
            "section_id": section.section_id,
            "title": section.title,
            "description": section.description,
            "chart_type": config.chart_type.value,
            "data": {}
        }
        
        # Apply aggregation if needed
        if config.x_axis and config.y_axis:
            grouped = df.groupby(config.x_axis)[config.y_axis]
            
            if config.aggregation == "sum":
                aggregated = grouped.sum()
            elif config.aggregation == "avg":
                aggregated = grouped.mean()
            elif config.aggregation == "count":
                aggregated = grouped.count()
            elif config.aggregation == "min":
                aggregated = grouped.min()
            elif config.aggregation == "max":
                aggregated = grouped.max()
            else:
                aggregated = grouped.sum()
            
            chart_data["data"] = {
                "x": aggregated.index.tolist(),
                "y": aggregated.values.tolist(),
                "x_label": config.x_axis,
                "y_label": config.y_axis
            }
        
        elif config.x_axis:  # Histogram or single-axis chart
            chart_data["data"] = {
                "x": df[config.x_axis].tolist(),
                "x_label": config.x_axis
            }
        
        # Add color data if specified
        if config.color_by:
            chart_data["data"]["color"] = df[config.color_by].tolist()
            chart_data["data"]["color_label"] = config.color_by
        
        return chart_data
