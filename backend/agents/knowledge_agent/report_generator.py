"""
Report Generator Module
Generates comprehensive EDA reports in Markdown and HTML formats
combining statistical analysis, insights, and visualizations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import base64
from io import BytesIO


class ReportGenerator:
    """
    Generates comprehensive Exploratory Data Analysis (EDA) reports
    in Markdown and HTML formats.
    """
    
    def __init__(self):
        """Initialize the Report Generator"""
        self.report_data = {}
        
    def generate_report(
        self,
        data: pd.DataFrame,
        profile_data: Dict[str, Any],
        insights: Dict[str, Any],
        recommendations: Dict[str, Any],
        format: str = 'markdown'
    ) -> str:
        """
        Generate a comprehensive EDA report.
        
        Args:
            data: Original DataFrame
            profile_data: Output from DataProfiler
            insights: Output from InsightGenerator
            recommendations: Output from RecommendationEngine
            format: 'markdown' or 'html'
            
        Returns:
            Report as string (Markdown or HTML)
        """
        self.report_data = {
            'data': data,
            'profile': profile_data,
            'insights': insights,
            'recommendations': recommendations,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if format.lower() == 'html':
            return self._generate_html_report()
        else:
            return self._generate_markdown_report()
    
    def _generate_markdown_report(self) -> str:
        """Generate report in Markdown format"""
        md = []
        
        # Title and metadata
        md.append(self._md_header())
        md.append(self._md_executive_summary())
        md.append(self._md_data_overview())
        md.append(self._md_data_quality())
        md.append(self._md_numeric_analysis())
        md.append(self._md_categorical_analysis())
        md.append(self._md_temporal_analysis())
        md.append(self._md_correlations())
        md.append(self._md_outliers())
        md.append(self._md_missing_data())
        md.append(self._md_key_insights())
        md.append(self._md_recommendations())
        md.append(self._md_next_steps())
        md.append(self._md_footer())
        
        return '\n\n'.join(md)
    
    def _md_header(self) -> str:
        """Generate report header"""
        return f"""# Exploratory Data Analysis Report

**Generated:** {self.report_data['generated_at']}  
**Tool:** DataCue Knowledge Agent  
**Version:** 1.0.0

---"""
    
    def _md_executive_summary(self) -> str:
        """Generate executive summary section"""
        summary = self.report_data['insights'].get('executive_summary', 'No summary available.')
        key_findings = self.report_data['insights'].get('key_findings', [])
        
        md = ["## Executive Summary\n", summary]
        
        if key_findings:
            md.append("\n### Key Findings\n")
            for finding in key_findings:
                md.append(f"- {finding}")
        
        return '\n'.join(md)
    
    def _md_data_overview(self) -> str:
        """Generate data overview section"""
        basic = self.report_data['profile']['basic_info']
        
        return f"""## Data Overview

| Metric | Value |
|--------|-------|
| **Rows** | {basic['num_rows']:,} |
| **Columns** | {basic['num_columns']} |
| **Memory Usage** | {basic['memory_usage_mb']:.2f} MB |
| **Duplicate Rows** | {basic['duplicate_rows']:,} |
| **Total Missing Values** | {basic['total_missing_values']:,} ({basic['missing_percentage']:.2f}%) |

### Column Types

{self._format_column_types(basic['column_types'])}"""
    
    def _format_column_types(self, col_types: Dict) -> str:
        """Format column types as a table"""
        if not col_types:
            return "No column type information available."
        
        lines = ["| Type | Count |", "|------|-------|"]
        for dtype, count in col_types.items():
            lines.append(f"| {dtype} | {count} |")
        return '\n'.join(lines)
    
    def _md_data_quality(self) -> str:
        """Generate data quality section"""
        quality = self.report_data['profile']['data_quality']
        
        md = [f"""## Data Quality Assessment

### Overall Quality Score: {quality['overall_quality_score']:.1f}/100
**Grade:** {quality['quality_grade']}

| Metric | Score |
|--------|-------|
| Completeness | {quality['completeness_score']:.1f}% |
| Uniqueness | {quality['uniqueness_score']:.1f}% |
| Consistency | {quality['consistency_score']:.1f}% |

### Quality Recommendations
"""]
        
        for rec in quality['recommendations']:
            md.append(f"- {rec}")
        
        return '\n'.join(md)
    
    def _md_numeric_analysis(self) -> str:
        """Generate numeric analysis section"""
        numeric_profile = self.report_data['profile'].get('numeric_profile', {})
        
        if not numeric_profile:
            return "## Numeric Columns\n\nNo numeric columns found in the dataset."
        
        md = ["## Numeric Columns Analysis\n"]
        md.append(f"**Total Numeric Columns:** {len(numeric_profile)}\n")
        
        # Create summary table
        md.append("| Column | Mean | Median | Std Dev | Min | Max | Missing % |")
        md.append("|--------|------|--------|---------|-----|-----|-----------|")
        
        for col, stats in list(numeric_profile.items())[:20]:  # Limit to 20
            md.append(
                f"| {col} | {stats['mean']:.2f} | {stats['median']:.2f} | "
                f"{stats['std']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} | "
                f"{stats['missing_pct']:.1f}% |"
            )
        
        # Add insights
        numeric_insights = self.report_data['insights'].get('numeric_insights', [])
        if numeric_insights:
            md.append("\n### Numeric Insights\n")
            for insight in numeric_insights[:10]:  # Top 10
                severity_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️',
                    'warning': '⚠️'
                }.get(insight.get('severity', 'info'), 'ℹ️')
                
                md.append(f"{severity_emoji} {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_categorical_analysis(self) -> str:
        """Generate categorical analysis section"""
        cat_profile = self.report_data['profile'].get('categorical_profile', {})
        
        if not cat_profile:
            return "## Categorical Columns\n\nNo categorical columns found in the dataset."
        
        md = ["## Categorical Columns Analysis\n"]
        md.append(f"**Total Categorical Columns:** {len(cat_profile)}\n")
        
        # Create summary table
        md.append("| Column | Unique Values | Cardinality | Most Common | Frequency | Missing % |")
        md.append("|--------|---------------|-------------|-------------|-----------|-----------|")
        
        for col, stats in list(cat_profile.items())[:15]:  # Limit to 15
            most_common = str(stats.get('most_common', 'N/A'))[:20]  # Truncate long values
            md.append(
                f"| {col} | {stats['unique_values']} | {stats['cardinality']} | "
                f"{most_common} | {stats['most_common_freq']} | {stats['missing_pct']:.1f}% |"
            )
        
        # Add insights
        cat_insights = self.report_data['insights'].get('categorical_insights', [])
        if cat_insights:
            md.append("\n### Categorical Insights\n")
            for insight in cat_insights[:10]:  # Top 10
                severity_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️',
                    'warning': '⚠️'
                }.get(insight.get('severity', 'info'), 'ℹ️')
                
                md.append(f"{severity_emoji} {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_temporal_analysis(self) -> str:
        """Generate temporal analysis section"""
        datetime_profile = self.report_data['profile'].get('datetime_profile', {})
        
        if not datetime_profile:
            return "## Temporal Analysis\n\nNo datetime columns found in the dataset."
        
        md = ["## Temporal Analysis\n"]
        md.append(f"**Total Datetime Columns:** {len(datetime_profile)}\n")
        
        for col, stats in datetime_profile.items():
            md.append(f"### {col}\n")
            md.append(f"- **Date Range:** {stats['min_date']} to {stats['max_date']}")
            md.append(f"- **Span:** {stats['date_range_days']} days")
            md.append(f"- **Unique Dates:** {stats['unique_dates']:,}")
            md.append(f"- **Has Time Component:** {'Yes' if stats['has_time_component'] else 'No'}")
            md.append("")
        
        # Add insights
        temporal_insights = self.report_data['insights'].get('temporal_insights', [])
        if temporal_insights:
            md.append("### Temporal Insights\n")
            for insight in temporal_insights:
                md.append(f"- {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_correlations(self) -> str:
        """Generate correlations section"""
        corr_data = self.report_data['profile'].get('correlations', {})
        strong_corrs = corr_data.get('strong_correlations', [])
        
        md = ["## Correlation Analysis\n"]
        md.append(f"**Strong Correlations Detected:** {len(strong_corrs)}\n")
        
        if strong_corrs:
            md.append("### Top Correlations\n")
            md.append("| Variable 1 | Variable 2 | Pearson | Spearman | Strength | Direction |")
            md.append("|------------|------------|---------|----------|----------|-----------|")
            
            for corr in strong_corrs[:15]:  # Top 15
                md.append(
                    f"| {corr['variable_1']} | {corr['variable_2']} | "
                    f"{corr['pearson']:.3f} | {corr['spearman']:.3f} | "
                    f"{corr['strength']} | {corr['direction']} |"
                )
        else:
            md.append("No strong correlations found (threshold: 0.7).")
        
        # Add insights
        corr_insights = self.report_data['insights'].get('correlation_insights', [])
        if corr_insights:
            md.append("\n### Correlation Insights\n")
            for insight in corr_insights:
                md.append(f"- {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_outliers(self) -> str:
        """Generate outliers section"""
        outliers = self.report_data['profile'].get('outliers', {})
        
        md = ["## Outlier Detection\n"]
        
        # Find columns with significant outliers
        significant_outliers = [
            (col, stats) for col, stats in outliers.items()
            if stats.get('iqr_outlier_pct', 0) > 1
        ]
        
        if significant_outliers:
            md.append("### Columns with Outliers (IQR Method)\n")
            md.append("| Column | Outliers | Percentage | IQR Bounds |")
            md.append("|--------|----------|------------|------------|")
            
            for col, stats in significant_outliers[:15]:
                md.append(
                    f"| {col} | {stats['iqr_outliers']} | {stats['iqr_outlier_pct']:.2f}% | "
                    f"[{stats['iqr_lower_bound']:.2f}, {stats['iqr_upper_bound']:.2f}] |"
                )
        else:
            md.append("No significant outliers detected.")
        
        # Add insights
        outlier_insights = self.report_data['insights'].get('outlier_insights', [])
        if outlier_insights:
            md.append("\n### Outlier Insights\n")
            for insight in outlier_insights:
                md.append(f"- {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_missing_data(self) -> str:
        """Generate missing data section"""
        missing = self.report_data['profile'].get('missing_patterns', {})
        
        md = ["## Missing Data Analysis\n"]
        md.append(f"**Total Missing Values:** {missing['total_missing']:,}\n")
        
        cols_with_missing = missing.get('columns_with_missing_pct', {})
        if cols_with_missing:
            md.append("### Columns with Missing Data\n")
            md.append("| Column | Missing Count | Percentage |")
            md.append("|--------|---------------|------------|")
            
            # Sort by percentage
            sorted_missing = sorted(cols_with_missing.items(), key=lambda x: x[1], reverse=True)
            
            for col, pct in sorted_missing[:20]:  # Top 20
                count = missing['columns_with_missing'].get(col, 0)
                md.append(f"| {col} | {count:,} | {pct:.2f}% |")
        else:
            md.append("✅ No missing data detected!")
        
        md.append(f"\n**Complete Rows:** {missing['complete_rows']:,} ({missing['complete_rows_pct']:.2f}%)")
        
        # Add insights
        missing_insights = self.report_data['insights'].get('missing_data_insights', [])
        if missing_insights:
            md.append("\n### Missing Data Insights\n")
            for insight in missing_insights:
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️',
                    'positive': '✅'
                }.get(insight.get('severity', 'info'), 'ℹ️')
                
                md.append(f"{severity_emoji} {insight['insight']}")
        
        return '\n'.join(md)
    
    def _md_key_insights(self) -> str:
        """Generate key insights section"""
        anomalies = self.report_data['insights'].get('anomalies', [])
        llm_narrative = self.report_data['insights'].get('llm_narrative', '')
        
        md = ["## Key Insights & Findings\n"]
        
        if llm_narrative and llm_narrative != "LLM not configured. Set API key to enable AI-powered narratives.":
            md.append("### AI-Generated Narrative\n")
            md.append(llm_narrative)
            md.append("")
        
        if anomalies:
            md.append("### Anomalies Detected\n")
            for anomaly in anomalies:
                md.append(f"⚠️ **{anomaly.get('column', 'Unknown')}**: {anomaly.get('anomaly', '')}")
        
        return '\n'.join(md)
    
    def _md_recommendations(self) -> str:
        """Generate recommendations section"""
        recs = self.report_data['recommendations']
        
        md = ["## Recommendations\n"]
        
        # Preprocessing
        if recs.get('preprocessing'):
            md.append("### Preprocessing Steps\n")
            for rec in recs['preprocessing'][:5]:
                md.append(f"**{rec['step'].upper()}** (Priority: {rec['priority']})")
                md.append(f"- {rec['description']}")
                md.append("")
        
        # Visualization
        if recs.get('visualization'):
            md.append("### Recommended Visualizations\n")
            for viz in recs['visualization'][:5]:
                md.append(f"**{viz['title']}** ({viz['type']})")
                md.append(f"- {viz['description']}")
                md.append(f"- Priority: {viz['priority']}")
                md.append("")
        
        # Modeling
        if recs.get('modeling'):
            md.append("### Suggested Modeling Approaches\n")
            for model in recs['modeling'][:3]:
                md.append(f"**{model['task'].upper()}**")
                md.append(f"- {model['description']}")
                if 'recommended_models' in model:
                    md.append(f"- Models: {', '.join(model['recommended_models'][:3])}")
                md.append("")
        
        return '\n'.join(md)
    
    def _md_next_steps(self) -> str:
        """Generate next steps section"""
        next_steps = self.report_data['recommendations'].get('next_steps', [])
        
        md = ["## Recommended Next Steps\n"]
        
        for step in next_steps:
            priority_emoji = {
                'critical': '🔴',
                'high': '🔵',
                'medium': '🟡',
                'low': '🟢'
            }.get(step.get('priority', 'medium'), '🔵')
            
            md.append(f"{priority_emoji} **{step['step']}**")
            md.append(f"   {step['description']}")
            md.append("")
        
        return '\n'.join(md)
    
    def _md_footer(self) -> str:
        """Generate report footer"""
        return f"""---

## About This Report

This report was automatically generated by the **DataCue Knowledge Agent** on {self.report_data['generated_at']}.

The analysis includes:
- Comprehensive data profiling
- Statistical analysis
- Pattern discovery
- AI-powered insights
- Actionable recommendations

For questions or feedback, please contact the DataCue team.
"""
    
    def _generate_html_report(self) -> str:
        """Generate report in HTML format"""
        # Get markdown version
        markdown_content = self._generate_markdown_report()
        
        # Wrap in HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EDA Report - DataCue</title>
    <style>
        {self._get_html_styles()}
    </style>
</head>
<body>
    <div class="container">
        <div class="markdown-body">
            {self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown to HTML (basic implementation).
        For production, use a library like markdown2 or mistune.
        """
        try:
            import markdown
            return markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
        except ImportError:
            # Fallback: basic conversion
            html = markdown_text
            html = html.replace('###', '<h3>').replace('##', '<h2>').replace('#', '<h1>')
            html = html.replace('\n\n', '</p><p>')
            html = html.replace('**', '<strong>').replace('*', '<em>')
            return f'<div>{html}</div>'
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background-color: #f6f8fa;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 980px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        .markdown-body {
            font-size: 16px;
        }
        h1 {
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 0.3em;
            font-size: 2em;
            margin-bottom: 16px;
        }
        h2 {
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 0.3em;
            font-size: 1.5em;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        h3 {
            font-size: 1.25em;
            margin-top: 20px;
            margin-bottom: 12px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        table th {
            background-color: #f6f8fa;
            font-weight: 600;
            padding: 8px 13px;
            border: 1px solid #d1d5da;
        }
        table td {
            padding: 8px 13px;
            border: 1px solid #d1d5da;
        }
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        code {
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            padding: 2px 6px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 85%;
        }
        ul, ol {
            padding-left: 2em;
        }
        li {
            margin: 4px 0;
        }
        hr {
            border: 0;
            border-top: 1px solid #e1e4e8;
            margin: 24px 0;
        }
        .emoji {
            font-size: 1.2em;
        }
        """
    
    def save_report(self, filepath: str, format: str = 'markdown'):
        """
        Save the generated report to a file.
        
        Args:
            filepath: Path to save the report
            format: 'markdown' or 'html'
        """
        report_content = self.generate_report(
            self.report_data.get('data'),
            self.report_data.get('profile'),
            self.report_data.get('insights'),
            self.report_data.get('recommendations'),
            format=format
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filepath
