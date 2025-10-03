"""
Dashboard Exporter
Export dashboards to PDF/PNG and save/load configurations
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
import os
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DashboardExporter:
    """
    Handles dashboard export to various formats and configuration persistence
    """
    
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize exporter
        
        Args:
            export_dir: Directory for exported files
        """
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def save_dashboard_config(
        self,
        dashboard_config: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Save dashboard configuration to JSON file
        
        Args:
            dashboard_config: Complete dashboard configuration
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        try:
            if not filename:
                dashboard_id = dashboard_config.get('dashboard_id', 'dashboard')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{dashboard_id}_{timestamp}.json"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # Prepare config for export (convert numpy/datetime types)
            export_config = self._prepare_config_for_export(dashboard_config)
            
            # Use custom JSON encoder for any remaining datetime objects
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (datetime, pd.Timestamp)):
                        return obj.isoformat()
                    if isinstance(obj, np.ndarray):
                        return obj.tolist()
                    if isinstance(obj, (np.integer, np.floating)):
                        return float(obj)
                    if pd.isna(obj):
                        return None
                    return super().default(obj)
            
            with open(filepath, 'w') as f:
                json.dump(export_config, f, indent=2, cls=DateTimeEncoder)
            
            logger.info(f"Dashboard config saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving dashboard config: {str(e)}")
            raise
    
    def load_dashboard_config(self, filepath: str) -> Dict[str, Any]:
        """
        Load dashboard configuration from JSON file
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            Dashboard configuration dictionary
        """
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Dashboard config loaded from: {filepath}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading dashboard config: {str(e)}")
            raise
    
    def export_to_png(
        self,
        dashboard_config: Dict[str, Any],
        chart_id: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        skip_if_unavailable: bool = True
    ) -> str:
        """
        Export chart(s) to PNG
        
        Args:
            dashboard_config: Dashboard configuration
            chart_id: Specific chart ID (if None, exports all)
            width: Image width in pixels
            height: Image height in pixels
            skip_if_unavailable: Skip PNG export if kaleido not available
            
        Returns:
            Path to exported file(s) or None if skipped
        """
        try:
            import plotly.graph_objects as go
            from plotly.io import write_image
            
            # Test if kaleido is available
            try:
                import kaleido
            except ImportError:
                msg = "kaleido package not installed. Skipping PNG export. Install with: pip install kaleido"
                if skip_if_unavailable:
                    logger.warning(msg)
                    return None
                else:
                    raise ImportError(msg)
            
            charts = dashboard_config.get('charts', [])
            
            if chart_id:
                # Export single chart
                chart = next((c for c in charts if c['id'] == chart_id), None)
                if not chart:
                    raise ValueError(f"Chart {chart_id} not found")
                
                return self._export_chart_png(chart, width, height)
            else:
                # Export all charts
                exported_files = []
                for chart in charts:
                    try:
                        filepath = self._export_chart_png(chart, width, height)
                        if filepath:
                            exported_files.append(filepath)
                    except Exception as e:
                        logger.warning(f"Failed to export {chart['id']}: {str(e)}")
                
                logger.info(f"Exported {len(exported_files)} charts to PNG")
                return exported_files if exported_files else None
                
        except ImportError as e:
            logger.error(f"PNG export unavailable: {str(e)}")
            if not skip_if_unavailable:
                raise
            return None
        except Exception as e:
            logger.error(f"Error exporting to PNG: {str(e)}")
            raise
    
    def _export_chart_png(
        self,
        chart: Dict[str, Any],
        width: int,
        height: int
    ) -> str:
        """Export single chart to PNG"""
        from plotly.io import write_image
        import plotly.graph_objects as go
        
        chart_id = chart['id']
        figure_dict = chart.get('figure', {})
        
        # Recreate figure from dict
        fig = go.Figure(figure_dict)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{chart_id}_{timestamp}.png"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export
        write_image(fig, filepath, width=width, height=height)
        
        logger.info(f"Chart {chart_id} exported to: {filepath}")
        return filepath
    
    def export_to_pdf(
        self,
        dashboard_config: Dict[str, Any],
        filename: Optional[str] = None,
        include_insights: bool = True,
        skip_if_unavailable: bool = True
    ) -> str:
        """
        Export dashboard to PDF (requires reportlab and kaleido)
        
        Args:
            dashboard_config: Dashboard configuration
            filename: Optional custom filename
            include_insights: Include narrative insights
            skip_if_unavailable: Skip if dependencies not available
            
        Returns:
            Path to PDF file or None if skipped
        """
        try:
            # Check for reportlab
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib.enums import TA_CENTER, TA_LEFT
            except ImportError:
                msg = "reportlab package not installed. Install with: pip install reportlab"
                if skip_if_unavailable:
                    logger.warning(msg)
                    return None
                else:
                    raise ImportError(msg)
            
            # Check for kaleido (needed for chart images)
            try:
                import kaleido
            except ImportError:
                msg = "kaleido package not installed. Install with: pip install kaleido"
                if skip_if_unavailable:
                    logger.warning(msg)
                    return None
                else:
                    raise ImportError(msg)
            
            if not filename:
                dashboard_id = dashboard_config.get('dashboard_id', 'dashboard')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{dashboard_id}_{timestamp}.pdf"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='#1f77b4',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor='#333333',
                spaceBefore=20,
                spaceAfter=10
            )
            
            # Title
            title = dashboard_config.get('title', 'Dashboard Report')
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Metadata
            metadata_text = f"""
            <b>Dashboard ID:</b> {dashboard_config.get('dashboard_id', 'N/A')}<br/>
            <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>Total Charts:</b> {len(dashboard_config.get('charts', []))}<br/>
            <b>Data Quality:</b> {dashboard_config.get('quality_indicators', {}).get('overall_score', 'N/A')}%
            """
            story.append(Paragraph(metadata_text, styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Export charts to temp PNG files first
            temp_images = []
            charts = dashboard_config.get('charts', [])
            
            for chart in charts:
                try:
                    # Chart title
                    story.append(Paragraph(chart.get('title', 'Chart'), heading_style))
                    
                    # Export chart as image
                    img_path = self._export_chart_png(chart, 800, 500)
                    temp_images.append(img_path)
                    
                    # Add image to PDF
                    img = Image(img_path, width=6*inch, height=3.75*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Add insights if available
                    if include_insights and 'ai_insights' in chart:
                        insights = chart['ai_insights']
                        narrative = insights.get('narrative', '')
                        if narrative:
                            story.append(Paragraph(f"<b>Insights:</b> {narrative}", styles['Normal']))
                            story.append(Spacer(1, 0.2*inch))
                    
                    # Page break after each chart
                    story.append(PageBreak())
                    
                except Exception as e:
                    logger.warning(f"Failed to add chart {chart.get('id', 'unknown')} to PDF: {str(e)}")
            
            # Build PDF
            doc.build(story)
            
            # Cleanup temp images
            for img_path in temp_images:
                try:
                    os.remove(img_path)
                except:
                    pass
            
            logger.info(f"Dashboard exported to PDF: {filepath}")
            return filepath
            
        except ImportError:
            logger.error("reportlab package required for PDF export. Install with: pip install reportlab")
            raise
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
    
    def export_to_html(
        self,
        dashboard_config: Dict[str, Any],
        filename: Optional[str] = None,
        standalone: bool = True
    ) -> str:
        """
        Export dashboard to interactive HTML
        
        Args:
            dashboard_config: Dashboard configuration
            filename: Optional custom filename
            standalone: Include all dependencies in single file
            
        Returns:
            Path to HTML file
        """
        try:
            if not filename:
                dashboard_id = dashboard_config.get('dashboard_id', 'dashboard')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{dashboard_id}_{timestamp}.html"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # Build HTML content
            html_content = self._build_html_dashboard(dashboard_config, standalone)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Dashboard exported to HTML: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to HTML: {str(e)}")
            raise
    
    def _build_html_dashboard(
        self,
        dashboard_config: Dict[str, Any],
        standalone: bool
    ) -> str:
        """Build HTML content for dashboard"""
        import plotly.graph_objects as go
        
        title = dashboard_config.get('title', 'Dashboard')
        charts = dashboard_config.get('charts', [])
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"    <title>{title}</title>",
            "    <meta charset='utf-8'>",
        ]
        
        if standalone:
            html_parts.append("    <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>")
        
        html_parts.extend([
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            "        .dashboard-header { text-align: center; padding: 20px; background: white; margin-bottom: 20px; }",
            "        .chart-container { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "        .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }",
            "        .chart-insights { color: #666; margin-top: 10px; padding: 10px; background: #f9f9f9; border-left: 3px solid #1f77b4; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <div class='dashboard-header'>",
            f"        <h1>{title}</h1>",
            f"        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"    </div>",
        ])
        
        # Add each chart
        for idx, chart in enumerate(charts):
            chart_id = f"chart_{idx}"
            title_text = chart.get('title', 'Chart')
            
            html_parts.extend([
                f"    <div class='chart-container'>",
                f"        <div class='chart-title'>{title_text}</div>",
                f"        <div id='{chart_id}'></div>",
            ])
            
            # Add insights if available
            if 'ai_insights' in chart:
                narrative = chart['ai_insights'].get('narrative', '')
                if narrative:
                    html_parts.append(f"        <div class='chart-insights'><b>Insights:</b> {narrative}</div>")
            
            html_parts.append(f"    </div>")
            
            # Add Plotly figure
            fig_dict = chart.get('figure', {})
            html_parts.extend([
                f"    <script>",
                f"        var figure_{idx} = {json.dumps(fig_dict)};",
                f"        Plotly.newPlot('{chart_id}', figure_{idx}.data, figure_{idx}.layout);",
                f"    </script>",
            ])
        
        html_parts.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _prepare_config_for_export(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare config for export by removing/simplifying large objects
        and converting numpy types to native Python types
        """
        import copy
        export_config = copy.deepcopy(config)
        
        # Convert numpy types to native Python types recursively
        export_config = self._convert_numpy_types(export_config)
        
        # Simplify charts (keep metadata but can optionally strip figure data)
        if 'charts' in export_config:
            simplified_charts = []
            for chart in export_config['charts']:
                chart_copy = chart.copy()
                # Keep figure for now (needed for exports)
                # To reduce file size, you could remove it: chart_copy.pop('figure', None)
                simplified_charts.append(chart_copy)
            export_config['charts'] = simplified_charts
        
        # Add export metadata
        export_config['export_info'] = {
            "exported_at": datetime.now().isoformat(),
            "exporter_version": "3.0.0",
            "format": "json"
        }
        
        return export_config
    
    def _convert_numpy_types(self, obj: Any) -> Any:
        """
        Recursively convert numpy types and datetime to native Python types for JSON serialization
        """
        import numpy as np
        import pandas as pd
        
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.str_, np.unicode_)):
            return str(obj)
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def get_export_summary(
        self,
        dashboard_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary of what can be exported
        
        Returns:
            Dictionary with export capabilities and file size estimates
        """
        charts_count = len(dashboard_config.get('charts', []))
        
        # Estimate file sizes (rough)
        config_size_kb = len(json.dumps(dashboard_config)) / 1024
        
        return {
            "charts_count": charts_count,
            "exportable_formats": ["JSON", "PNG", "PDF", "HTML"],
            "estimated_sizes": {
                "json_config": f"{config_size_kb:.1f} KB",
                "png_per_chart": "~200 KB",
                "pdf_full": f"~{charts_count * 250} KB",
                "html_interactive": f"~{config_size_kb * 1.5:.1f} KB"
            },
            "features": {
                "config_save_load": True,
                "png_export": True,
                "pdf_export": True,
                "html_export": True,
                "batch_export": True
            }
        }
