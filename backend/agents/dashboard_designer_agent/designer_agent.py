"""
Dashboard Designer Agent - AI-Powered Dashboard Generator
Uses Groq AI to intelligently generate dashboard configurations
"""
import os
import json
from typing import Dict, List, Optional
from groq import Groq
import pandas as pd

from models.dashboard_models import (
    DashboardConfig,
    TemplateSection,
    ChartOption,
    ChartType,
    SectionType,
    DatasetInfo
)
from agents.dashboard_designer_agent.data_analyzer import DataAnalyzer


class DashboardDesignerAgent:
    """AI agent for intelligent dashboard generation"""
    
    def __init__(self):
        # Initialize Groq client
        api_key = os.getenv("groq_api")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "mixtral-8x7b-32768"
        self.data_analyzer = DataAnalyzer()
    
    def generate_dashboard(
        self, 
        df: pd.DataFrame,
        dataset_id: str,
        user_prompt: Optional[str] = None
    ) -> tuple[DashboardConfig, str]:
        """
        Generate a complete dashboard configuration using AI
        
        Args:
            df: Dataset to create dashboard for
            dataset_id: Unique identifier for the dataset
            user_prompt: Optional user guidance for dashboard generation
            
        Returns:
            Tuple of (DashboardConfig, ai_reasoning)
        """
        # Analyze dataset
        dataset_info = self.data_analyzer.analyze_dataset(df, dataset_id)
        
        # Build AI prompt
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_prompt(dataset_info, user_prompt)
        
        # Call Groq AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response
            dashboard_config, reasoning = self._parse_ai_response(
                ai_response, 
                dataset_id, 
                dataset_info
            )
            
            return dashboard_config, reasoning
            
        except Exception as e:
            # Fallback to rule-based generation if AI fails
            print(f"AI generation failed: {str(e)}, using fallback")
            return self._generate_fallback_dashboard(df, dataset_id, dataset_info)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for AI"""
        return """You are an expert data analyst and dashboard designer. Your task is to analyze a dataset and create the perfect dashboard configuration.

For each dashboard, you should:
1. Identify the most important metrics and KPIs
2. Choose the right chart types for different insights
3. Create a logical layout and flow
4. Provide clear titles and descriptions

Available chart types:
- bar: For comparing categories
- line: For trends over time
- scatter: For correlations between variables
- pie: For proportions and percentages
- histogram: For distributions of numeric data
- box: For statistical distributions and outliers
- heatmap: For correlations or two-dimensional patterns
- area: For cumulative trends over time
- funnel: For sequential processes or conversion rates
- treemap: For hierarchical data

Respond ONLY with valid JSON in this exact format:
{
  "title": "Dashboard Title",
  "description": "Brief description",
  "reasoning": "Why you chose these visualizations",
  "sections": [
    {
      "section_id": "unique_id",
      "section_type": "kpi|chart|header",
      "title": "Section Title",
      "description": "What this shows",
      "position": 0,
      "size": "small|medium|large|full",
      "chart_type": "bar|line|etc",
      "x_axis": "column_name",
      "y_axis": "column_name",
      "color_by": "column_name (optional)",
      "aggregation": "sum|count|avg|min|max"
    }
  ]
}"""
    
    def _build_user_prompt(self, dataset_info: DatasetInfo, user_prompt: Optional[str]) -> str:
        """Build user prompt with dataset information"""
        
        # Categorize columns
        numeric_cols = [col for col, t in dataset_info.column_types.items() if t == "numeric"]
        categorical_cols = [col for col, t in dataset_info.column_types.items() if t == "categorical"]
        datetime_cols = [col for col, t in dataset_info.column_types.items() if t == "datetime"]
        
        prompt = f"""Analyze this dataset and create a dashboard:

Dataset Overview:
- Total Rows: {dataset_info.row_count}
- Total Columns: {len(dataset_info.columns)}

Column Types:
- Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:10])}{'...' if len(numeric_cols) > 10 else ''}
- Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:10])}{'...' if len(categorical_cols) > 10 else ''}
- Datetime columns ({len(datetime_cols)}): {', '.join(datetime_cols)}

Sample Data (first 3 rows):
{json.dumps({col: vals[:3] for col, vals in dataset_info.sample_data.items()}, indent=2)}
"""
        
        if user_prompt:
            prompt += f"\n\nUser Requirements:\n{user_prompt}\n"
        
        prompt += """
Create a dashboard with:
1. A header section
2. 3-4 KPI sections showing key metrics
3. 4-6 chart sections with different visualizations
4. Ensure charts use appropriate column types (datetime for time series, categorical for grouping, numeric for values)

Return only valid JSON, no other text."""
        
        return prompt
    
    def _parse_ai_response(
        self, 
        ai_response: str, 
        dataset_id: str,
        dataset_info: DatasetInfo
    ) -> tuple[DashboardConfig, str]:
        """Parse AI JSON response into DashboardConfig"""
        
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]
            
            data = json.loads(json_str)
            
            # Build sections
            sections = []
            for idx, section_data in enumerate(data.get('sections', [])):
                section = TemplateSection(
                    section_id=section_data.get('section_id', f'section_{idx}'),
                    section_type=SectionType(section_data.get('section_type', 'chart')),
                    title=section_data.get('title', 'Untitled'),
                    description=section_data.get('description', ''),
                    position=section_data.get('position', idx),
                    size=section_data.get('size', 'medium'),
                    required=True
                )
                
                # Add chart configuration if it's a chart section
                if section.section_type == SectionType.CHART:
                    chart_type = section_data.get('chart_type')
                    if chart_type:
                        section.chart_config = ChartOption(
                            chart_type=ChartType(chart_type),
                            x_axis=section_data.get('x_axis'),
                            y_axis=section_data.get('y_axis'),
                            color_by=section_data.get('color_by'),
                            aggregation=section_data.get('aggregation', 'sum'),
                            title=section_data.get('title'),
                            description=section_data.get('description')
                        )
                
                sections.append(section)
            
            # Create dashboard config
            dashboard_config = DashboardConfig(
                dashboard_id=f"dashboard_{dataset_id}",
                template_id="ai_generated",
                dataset_id=dataset_id,
                title=data.get('title', 'AI Generated Dashboard'),
                description=data.get('description', ''),
                sections=sections
            )
            
            reasoning = data.get('reasoning', 'AI-generated dashboard based on data analysis')
            
            return dashboard_config, reasoning
            
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            raise
    
    def _generate_fallback_dashboard(
        self, 
        df: pd.DataFrame,
        dataset_id: str,
        dataset_info: DatasetInfo
    ) -> tuple[DashboardConfig, str]:
        """Generate a simple rule-based dashboard if AI fails"""
        
        sections = []
        position = 0
        
        # Header
        sections.append(TemplateSection(
            section_id="header",
            section_type=SectionType.HEADER,
            title="Data Overview",
            description="Automated dashboard",
            position=position,
            size="full",
            required=True
        ))
        position += 1
        
        # Get column types
        numeric_cols = [col for col, t in dataset_info.column_types.items() if t == "numeric"]
        categorical_cols = [col for col, t in dataset_info.column_types.items() if t == "categorical"]
        datetime_cols = [col for col, t in dataset_info.column_types.items() if t == "datetime"]
        
        # Add KPIs for first 3 numeric columns
        for i, col in enumerate(numeric_cols[:3]):
            sections.append(TemplateSection(
                section_id=f"kpi_{i}",
                section_type=SectionType.KPI,
                title=col.replace('_', ' ').title(),
                description=f"Total {col}",
                position=position,
                size="small",
                required=True
            ))
            position += 1
        
        # Add time series if datetime column exists
        if datetime_cols and numeric_cols:
            sections.append(TemplateSection(
                section_id="time_series",
                section_type=SectionType.CHART,
                title=f"{numeric_cols[0]} Over Time",
                description="Trend analysis",
                position=position,
                size="large",
                required=True,
                chart_config=ChartOption(
                    chart_type=ChartType.LINE,
                    x_axis=datetime_cols[0],
                    y_axis=numeric_cols[0],
                    aggregation="sum"
                )
            ))
            position += 1
        
        # Add categorical breakdown if available
        if categorical_cols and numeric_cols:
            sections.append(TemplateSection(
                section_id="category_breakdown",
                section_type=SectionType.CHART,
                title=f"{numeric_cols[0]} by {categorical_cols[0]}",
                description="Category analysis",
                position=position,
                size="medium",
                required=True,
                chart_config=ChartOption(
                    chart_type=ChartType.BAR,
                    x_axis=categorical_cols[0],
                    y_axis=numeric_cols[0],
                    aggregation="sum"
                )
            ))
            position += 1
        
        # Add distribution for first numeric column
        if numeric_cols:
            sections.append(TemplateSection(
                section_id="distribution",
                section_type=SectionType.CHART,
                title=f"{numeric_cols[0]} Distribution",
                description="Data distribution",
                position=position,
                size="medium",
                required=True,
                chart_config=ChartOption(
                    chart_type=ChartType.HISTOGRAM,
                    x_axis=numeric_cols[0],
                    aggregation="count"
                )
            ))
        
        dashboard_config = DashboardConfig(
            dashboard_id=f"dashboard_{dataset_id}",
            template_id="fallback",
            dataset_id=dataset_id,
            title="Data Overview Dashboard",
            description="Automatically generated dashboard",
            sections=sections
        )
        
        reasoning = "Rule-based dashboard generated as fallback"
        
        return dashboard_config, reasoning
