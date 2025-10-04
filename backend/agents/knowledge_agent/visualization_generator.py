"""
Visualization Generator for Knowledge Agent
Creates interactive Plotly visualizations for data analysis.

Features:
- Interactive correlation heatmaps
- Distribution plots
- Scatter matrices
- Time series visualizations
- Customizable styling
- Export to HTML/PNG
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class VisualizationGenerator:
    """
    Generates interactive Plotly visualizations for data insights.
    
    Features:
    - Correlation heatmaps with annotations
    - Distribution plots (histograms, box plots, violin plots)
    - Scatter plots and scatter matrices
    - Time series line charts
    - Custom color schemes
    - Interactive tooltips and legends
    """
    
    def __init__(self, theme: str = 'plotly'):
        """
        Initialize visualization generator.
        
        Args:
            theme: Plotly theme ('plotly', 'plotly_white', 'plotly_dark', 'ggplot2', 'seaborn')
        """
        self.theme = theme
        self.color_schemes = {
            'default': px.colors.sequential.Viridis,
            'correlation': px.colors.diverging.RdBu_r,
            'categorical': px.colors.qualitative.Set2,
            'heatmap': px.colors.sequential.Blues
        }
    
    def create_correlation_heatmap(
        self,
        data: pd.DataFrame,
        method: str = 'pearson',
        title: Optional[str] = None,
        show_values: bool = True,
        min_corr: float = 0.0
    ) -> go.Figure:
        """
        Create interactive correlation heatmap.
        
        Args:
            data: DataFrame with numeric columns
            method: Correlation method ('pearson', 'spearman', 'kendall')
            title: Custom title
            show_values: Whether to show correlation values on cells
            min_corr: Minimum correlation threshold to display
            
        Returns:
            Plotly Figure object
        """
        # Select numeric columns
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            raise ValueError("No numeric columns found for correlation analysis")
        
        # Calculate correlation matrix
        corr_matrix = numeric_data.corr(method=method)
        
        # Apply threshold
        if min_corr > 0:
            corr_matrix = corr_matrix.where(abs(corr_matrix) >= min_corr, np.nan)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale=self.color_schemes['correlation'],
            zmid=0,  # Center at 0
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2) if show_values else None,
            texttemplate='%{text}' if show_values else None,
            textfont={"size": 10},
            colorbar=dict(
                title=dict(text=f"{method.capitalize()}<br>Correlation"),
                tickmode="linear",
                tick0=-1,
                dtick=0.5
            ),
            hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=title or f'{method.capitalize()} Correlation Matrix',
            xaxis_title='Variables',
            yaxis_title='Variables',
            template=self.theme,
            width=800,
            height=700,
            xaxis={'side': 'bottom'},
            yaxis={'autorange': 'reversed'}
        )
        
        return fig
    
    def create_distribution_plot(
        self,
        data: pd.DataFrame,
        column: str,
        plot_type: str = 'histogram',
        bins: int = 30,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Create distribution visualization.
        
        Args:
            data: DataFrame
            column: Column name to visualize
            plot_type: 'histogram', 'box', or 'violin'
            bins: Number of bins for histogram
            title: Custom title
            
        Returns:
            Plotly Figure object
        """
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")
        
        values = data[column].dropna()
        
        if plot_type == 'histogram':
            fig = go.Figure(data=[go.Histogram(
                x=values,
                nbinsx=bins,
                marker_color=self.color_schemes['default'][3],
                opacity=0.7,
                name=column,
                hovertemplate='Range: %{x}<br>Count: %{y}<extra></extra>'
            )])
            
            # Add mean and median lines
            mean_val = values.mean()
            median_val = values.median()
            
            fig.add_vline(
                x=mean_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_val:.2f}",
                annotation_position="top"
            )
            fig.add_vline(
                x=median_val,
                line_dash="dot",
                line_color="green",
                annotation_text=f"Median: {median_val:.2f}",
                annotation_position="bottom"
            )
            
            fig.update_xaxes(title=column)
            fig.update_yaxes(title='Frequency')
        
        elif plot_type == 'box':
            fig = go.Figure(data=[go.Box(
                y=values,
                name=column,
                marker_color=self.color_schemes['default'][4],
                boxmean='sd',  # Show mean and standard deviation
                hovertemplate='Value: %{y}<extra></extra>'
            )])
            fig.update_yaxes(title=column)
        
        elif plot_type == 'violin':
            fig = go.Figure(data=[go.Violin(
                y=values,
                name=column,
                box_visible=True,
                meanline_visible=True,
                fillcolor=self.color_schemes['default'][5],
                opacity=0.6,
                hovertemplate='Value: %{y}<extra></extra>'
            )])
            fig.update_yaxes(title=column)
        
        else:
            raise ValueError(f"Unknown plot type: {plot_type}")
        
        fig.update_layout(
            title=title or f'Distribution of {column}',
            template=self.theme,
            showlegend=False,
            width=800,
            height=500
        )
        
        return fig
    
    def create_scatter_plot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = None,
        size: Optional[str] = None,
        title: Optional[str] = None,
        trendline: bool = False
    ) -> go.Figure:
        """
        Create interactive scatter plot.
        
        Args:
            data: DataFrame
            x: X-axis column
            y: Y-axis column
            color: Column for color encoding
            size: Column for size encoding
            title: Custom title
            trendline: Whether to add trendline
            
        Returns:
            Plotly Figure object
        """
        fig = px.scatter(
            data,
            x=x,
            y=y,
            color=color,
            size=size,
            template=self.theme,
            title=title or f'{y} vs {x}',
            trendline='ols' if trendline else None,
            hover_data=data.columns
        )
        
        fig.update_traces(marker=dict(line=dict(width=0.5, color='white')))
        fig.update_layout(width=800, height=600)
        
        return fig
    
    def create_scatter_matrix(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        color: Optional[str] = None,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Create scatter plot matrix for multiple variables.
        
        Args:
            data: DataFrame
            columns: List of columns to include (default: all numeric)
            color: Column for color encoding
            title: Custom title
            
        Returns:
            Plotly Figure object
        """
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Limit to 6 columns for readability
        if len(columns) > 6:
            columns = columns[:6]
        
        fig = px.scatter_matrix(
            data,
            dimensions=columns,
            color=color,
            template=self.theme,
            title=title or 'Scatter Matrix'
        )
        
        fig.update_traces(diagonal_visible=False, showupperhalf=False)
        fig.update_layout(
            width=1000,
            height=1000,
            showlegend=True if color else False
        )
        
        return fig
    
    def create_time_series(
        self,
        data: pd.DataFrame,
        date_column: str,
        value_columns: List[str],
        title: Optional[str] = None,
        show_trend: bool = False
    ) -> go.Figure:
        """
        Create time series line chart.
        
        Args:
            data: DataFrame
            date_column: Column with datetime values
            value_columns: Columns to plot
            title: Custom title
            show_trend: Whether to show moving average
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        for i, col in enumerate(value_columns):
            fig.add_trace(go.Scatter(
                x=data[date_column],
                y=data[col],
                mode='lines+markers',
                name=col,
                line=dict(width=2),
                marker=dict(size=4),
                hovertemplate=f'{col}: %{{y}}<br>Date: %{{x}}<extra></extra>'
            ))
            
            if show_trend:
                # Add 7-day moving average
                ma = data[col].rolling(window=7).mean()
                fig.add_trace(go.Scatter(
                    x=data[date_column],
                    y=ma,
                    mode='lines',
                    name=f'{col} (7-day MA)',
                    line=dict(dash='dash', width=1.5),
                    opacity=0.7,
                    hovertemplate=f'{col} MA: %{{y}}<extra></extra>'
                ))
        
        fig.update_layout(
            title=title or 'Time Series Analysis',
            xaxis_title=date_column,
            yaxis_title='Value',
            template=self.theme,
            hovermode='x unified',
            width=1000,
            height=500
        )
        
        return fig
    
    def create_categorical_bar(
        self,
        data: pd.DataFrame,
        category_column: str,
        value_column: Optional[str] = None,
        aggregation: str = 'count',
        top_n: Optional[int] = None,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Create bar chart for categorical data.
        
        Args:
            data: DataFrame
            category_column: Categorical column
            value_column: Value column to aggregate
            aggregation: 'count', 'sum', 'mean', 'median'
            top_n: Show only top N categories
            title: Custom title
            
        Returns:
            Plotly Figure object
        """
        if value_column is None or aggregation == 'count':
            # Count frequency
            counts = data[category_column].value_counts()
        else:
            # Aggregate values
            if aggregation == 'sum':
                counts = data.groupby(category_column)[value_column].sum()
            elif aggregation == 'mean':
                counts = data.groupby(category_column)[value_column].mean()
            elif aggregation == 'median':
                counts = data.groupby(category_column)[value_column].median()
            else:
                raise ValueError(f"Unknown aggregation: {aggregation}")
        
        # Sort and limit
        counts = counts.sort_values(ascending=False)
        if top_n:
            counts = counts.head(top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=counts.index,
            y=counts.values,
            marker_color=self.color_schemes['categorical'],
            hovertemplate='%{x}<br>%{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title or f'{aggregation.capitalize()} by {category_column}',
            xaxis_title=category_column,
            yaxis_title=aggregation.capitalize(),
            template=self.theme,
            width=800,
            height=500
        )
        
        return fig
    
    def create_subplots_grid(
        self,
        figures: List[Tuple[go.Figure, str]],
        rows: int,
        cols: int,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Combine multiple plots into subplot grid.
        
        Args:
            figures: List of (figure, subplot_title) tuples
            rows: Number of rows
            cols: Number of columns
            title: Overall title
            
        Returns:
            Combined Plotly Figure
        """
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[title for _, title in figures]
        )
        
        for idx, (plot_fig, _) in enumerate(figures):
            row = (idx // cols) + 1
            col = (idx % cols) + 1
            
            for trace in plot_fig.data:
                fig.add_trace(trace, row=row, col=col)
        
        fig.update_layout(
            title_text=title or 'Analysis Dashboard',
            template=self.theme,
            showlegend=False,
            height=300 * rows,
            width=400 * cols
        )
        
        return fig
    
    def save_figure(
        self,
        fig: go.Figure,
        filepath: str,
        format: str = 'html',
        **kwargs
    ) -> None:
        """
        Save figure to file.
        
        Args:
            fig: Plotly figure
            filepath: Output file path
            format: 'html', 'png', 'pdf', 'svg', or 'jpeg'
            **kwargs: Additional arguments for image export
                - width: Image width (default: 1200)
                - height: Image height (default: 800)
                - scale: Image scale factor (default: 2 for high DPI)
        """
        if format == 'html':
            fig.write_html(filepath, include_plotlyjs='cdn')
        elif format in ['png', 'pdf', 'svg', 'jpeg', 'jpg']:
            # Set defaults for high-quality export
            width = kwargs.get('width', 1200)
            height = kwargs.get('height', 800)
            scale = kwargs.get('scale', 2)  # High DPI for print quality
            
            try:
                # Try using kaleido (preferred)
                fig.write_image(
                    filepath,
                    format=format if format != 'jpg' else 'jpeg',
                    width=width,
                    height=height,
                    scale=scale
                )
            except Exception as e:
                # Fallback message if kaleido not installed
                print(f"⚠️ Static image export requires 'kaleido' package.")
                print(f"   Install with: pip install kaleido")
                print(f"   Error: {e}")
                print(f"   Saving as HTML instead: {filepath.replace(f'.{format}', '.html')}")
                fig.write_html(filepath.replace(f'.{format}', '.html'), include_plotlyjs='cdn')
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'html', 'png', 'pdf', 'svg', or 'jpeg'")
    
    def create_comprehensive_dashboard(
        self,
        data: pd.DataFrame,
        profile_data: Optional[Dict] = None
    ) -> go.Figure:
        """
        Create comprehensive analysis dashboard.
        
        Args:
            data: DataFrame to visualize
            profile_data: Data profiling results
            
        Returns:
            Interactive dashboard figure
        """
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            raise ValueError("Need at least 2 numeric columns for dashboard")
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Correlation Heatmap',
                f'Distribution: {numeric_cols[0]}',
                f'{numeric_cols[1]} vs {numeric_cols[0]}',
                'Top Categories'
            ),
            specs=[
                [{'type': 'heatmap'}, {'type': 'histogram'}],
                [{'type': 'scatter'}, {'type': 'bar'}]
            ]
        )
        
        # 1. Correlation heatmap (simplified)
        corr = data[numeric_cols[:4]].corr()
        fig.add_trace(
            go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale=self.color_schemes['correlation'],
                showscale=False
            ),
            row=1, col=1
        )
        
        # 2. Distribution histogram
        fig.add_trace(
            go.Histogram(
                x=data[numeric_cols[0]],
                marker_color=self.color_schemes['default'][3],
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Scatter plot
        fig.add_trace(
            go.Scatter(
                x=data[numeric_cols[0]],
                y=data[numeric_cols[1]],
                mode='markers',
                marker=dict(size=5),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 4. Categorical bar (if available)
        cat_cols = data.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            counts = data[cat_cols[0]].value_counts().head(5)
            fig.add_trace(
                go.Bar(
                    x=counts.index,
                    y=counts.values,
                    marker_color=self.color_schemes['categorical'],
                    showlegend=False
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text='Data Analysis Dashboard',
            template=self.theme,
            height=800,
            width=1200,
            showlegend=False
        )
        
        return fig
    
    def __repr__(self) -> str:
        """String representation."""
        return f"VisualizationGenerator(theme='{self.theme}')"
