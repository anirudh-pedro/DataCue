"""
Chart Factory
Creates Plotly charts based on data and metadata recommendations
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ChartFactory:
    """
    Factory class for creating various types of Plotly charts
    Uses metadata recommendations to optimize chart generation
    """
    
    def __init__(self):
        self.color_scheme = px.colors.qualitative.Plotly
        self.template = "plotly_white"
    
    def create_histogram(
        self, 
        data: pd.DataFrame, 
        column: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a histogram for numeric distribution
        """
        try:
            fig = px.histogram(
                data,
                x=column,
                nbins=30,
                title=f"Distribution of {column.replace('_', ' ').title()}",
                template=self.template,
                labels={column: column.replace('_', ' ').title()}
            )
            
            fig.update_layout(
                xaxis_title=column.replace('_', ' ').title(),
                yaxis_title="Count",
                showlegend=False
            )
            
            return {
                "id": f"hist_{column}",
                "type": "histogram",
                "title": f"Distribution of {column.replace('_', ' ').title()}",
                "column": column,
                "figure": fig.to_dict(),
                "insights": self._generate_histogram_insights(data, column, metadata),
                "interactivity": {
                    "supports_drill_down": False,
                    "cross_filter_enabled": True,
                    "cross_filter_column": column,
                    "click_action": "filter_range"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating histogram for {column}: {str(e)}")
            return None
    
    def create_bar_chart(
        self, 
        data: pd.DataFrame, 
        column: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a bar chart for categorical data
        """
        try:
            # Get value counts
            value_counts = data[column].value_counts().head(10)  # Top 10
            
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"{column.replace('_', ' ').title()} Distribution",
                template=self.template,
                labels={'x': column.replace('_', ' ').title(), 'y': 'Count'}
            )
            
            fig.update_layout(
                xaxis_title=column.replace('_', ' ').title(),
                yaxis_title="Count",
                showlegend=False
            )
            
            return {
                "id": f"bar_{column}",
                "type": "bar",
                "title": f"{column.replace('_', ' ').title()} Distribution",
                "column": column,
                "figure": fig.to_dict(),
                "insights": {
                    "top_value": str(value_counts.index[0]),
                    "top_count": int(value_counts.values[0]),
                    "total_unique": int(metadata.get('unique_count', 0))
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "cross_filter_column": column,
                    "click_action": "filter_category",
                    "drill_down_config": {
                        "enabled": True,
                        "target_column": column,
                        "action": "Click a bar to filter all other charts"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating bar chart for {column}: {str(e)}")
            return None
    
    def create_time_series(
        self, 
        data: pd.DataFrame, 
        time_column: str,
        value_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a time series line chart
        """
        try:
            # Sort by time
            df_sorted = data.sort_values(time_column)
            
            fig = px.line(
                df_sorted,
                x=time_column,
                y=value_column,
                title=f"{value_column.replace('_', ' ').title()} Over Time",
                template=self.template,
                labels={
                    time_column: "Date",
                    value_column: value_column.replace('_', ' ').title()
                }
            )
            
            fig.update_traces(line_color=self.color_scheme[0])
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title=value_column.replace('_', ' ').title(),
                hovermode='x unified'
            )
            
            return {
                "id": f"timeseries_{time_column}_{value_column}",
                "type": "time_series",
                "title": f"{value_column.replace('_', ' ').title()} Over Time",
                "columns": {"time": time_column, "value": value_column},
                "figure": fig.to_dict(),
                "insights": self._generate_timeseries_insights(df_sorted, time_column, value_column),
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "cross_filter_column": time_column,
                    "click_action": "filter_date_range",
                    "drill_down_config": {
                        "enabled": True,
                        "target_column": time_column,
                        "action": "Click a point to zoom into time period"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating time series: {str(e)}")
            return None
    
    def create_correlation_heatmap(
        self, 
        data: pd.DataFrame,
        correlation_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a correlation heatmap
        """
        try:
            # Get numeric columns only
            numeric_data = data.select_dtypes(include=['number'])
            
            if numeric_data.shape[1] < 2:
                return None
            
            # Calculate correlation
            corr_matrix = numeric_data.corr()
            
            fig = px.imshow(
                corr_matrix,
                title="Correlation Heatmap",
                template=self.template,
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto"
            )
            
            fig.update_layout(
                xaxis_title="",
                yaxis_title="",
                coloraxis_colorbar=dict(title="Correlation")
            )
            
            return {
                "id": "correlation_heatmap",
                "type": "heatmap",
                "title": "Correlation Heatmap",
                "figure": fig.to_dict(),
                "insights": {
                    "strong_correlations": correlation_data.get('strong_correlations', []),
                    "columns_analyzed": correlation_data.get('columns_analyzed', [])
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": False,
                    "click_action": "show_scatter",
                    "drill_down_config": {
                        "enabled": True,
                        "action": "Click a cell to see scatter plot of those two variables"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {str(e)}")
            return None
    
    def create_grouped_bar(
        self, 
        data: pd.DataFrame,
        category_column: str,
        value_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create grouped bar chart (category vs measure)
        """
        try:
            # Aggregate data
            grouped = data.groupby(category_column)[value_column].agg(['sum', 'mean', 'count']).reset_index()
            
            fig = go.Figure()
            
            # Add bars for sum
            fig.add_trace(go.Bar(
                x=grouped[category_column],
                y=grouped['sum'],
                name='Total',
                marker_color=self.color_scheme[0]
            ))
            
            # Add bars for average
            fig.add_trace(go.Bar(
                x=grouped[category_column],
                y=grouped['mean'],
                name='Average',
                marker_color=self.color_scheme[1]
            ))
            
            fig.update_layout(
                title=f"{value_column.replace('_', ' ').title()} by {category_column.replace('_', ' ').title()}",
                xaxis_title=category_column.replace('_', ' ').title(),
                yaxis_title=value_column.replace('_', ' ').title(),
                barmode='group',
                template=self.template
            )
            
            return {
                "id": f"grouped_{category_column}_{value_column}",
                "type": "grouped_bar",
                "title": f"{value_column.replace('_', ' ').title()} by {category_column.replace('_', ' ').title()}",
                "columns": {"category": category_column, "value": value_column},
                "figure": fig.to_dict(),
                "insights": {
                    "top_category": str(grouped.loc[grouped['sum'].idxmax(), category_column]),
                    "max_value": float(grouped['sum'].max()),
                    "categories_count": len(grouped)
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "cross_filter_column": category_column,
                    "click_action": "filter_category",
                    "drill_down_config": {
                        "enabled": True,
                        "target_column": category_column,
                        "action": "Click a bar to filter dashboard by category"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating grouped bar chart: {str(e)}")
            return None
    
    def create_pie_chart(
        self, 
        data: pd.DataFrame,
        column: str,
        top_n: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pie chart for categorical distribution
        """
        try:
            value_counts = data[column].value_counts().head(top_n)
            
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"{column.replace('_', ' ').title()} Distribution",
                template=self.template
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            return {
                "id": f"pie_{column}",
                "type": "pie",
                "title": f"{column.replace('_', ' ').title()} Distribution",
                "column": column,
                "figure": fig.to_dict(),
                "insights": {
                    "dominant_category": str(value_counts.index[0]),
                    "dominant_percentage": round(value_counts.values[0] / value_counts.sum() * 100, 1)
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "cross_filter_column": column,
                    "click_action": "filter_category",
                    "drill_down_config": {
                        "enabled": True,
                        "target_column": column,
                        "action": "Click a slice to filter by that category"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating pie chart: {str(e)}")
            return None
    
    def create_box_plot(
        self, 
        data: pd.DataFrame,
        column: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a box plot for numeric distribution analysis
        """
        try:
            fig = px.box(
                data,
                y=column,
                title=f"{column.replace('_', ' ').title()} Distribution (Box Plot)",
                template=self.template
            )
            
            fig.update_layout(
                yaxis_title=column.replace('_', ' ').title(),
                showlegend=False
            )
            
            return {
                "id": f"box_{column}",
                "type": "box_plot",
                "title": f"{column.replace('_', ' ').title()} Distribution",
                "column": column,
                "figure": fig.to_dict(),
                "insights": {
                    "median": float(metadata.get('median', 0)),
                    "q25": float(metadata.get('q25', 0)),
                    "q75": float(metadata.get('q75', 0)),
                    "outliers_detected": metadata.get('negative_count', 0) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating box plot: {str(e)}")
            return None
    
    def create_scatter_plot(
        self, 
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a scatter plot for numeric vs numeric analysis
        Auto-calculates correlation coefficient
        """
        try:
            # Calculate correlation
            correlation = data[[x_column, y_column]].corr().iloc[0, 1]
            
            # Create scatter plot
            if color_column:
                fig = px.scatter(
                    data,
                    x=x_column,
                    y=y_column,
                    color=color_column,
                    title=f"{y_column.replace('_', ' ').title()} vs {x_column.replace('_', ' ').title()}",
                    template=self.template,
                    labels={
                        x_column: x_column.replace('_', ' ').title(),
                        y_column: y_column.replace('_', ' ').title()
                    }
                )
            else:
                fig = px.scatter(
                    data,
                    x=x_column,
                    y=y_column,
                    title=f"{y_column.replace('_', ' ').title()} vs {x_column.replace('_', ' ').title()}",
                    template=self.template,
                    labels={
                        x_column: x_column.replace('_', ' ').title(),
                        y_column: y_column.replace('_', ' ').title()
                    }
                )
                fig.update_traces(marker=dict(color=self.color_scheme[0]))
            
            # Add trendline for strong correlations
            if abs(correlation) > 0.5:
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    data[x_column].dropna(), 
                    data[y_column].dropna()
                )
                line_x = [data[x_column].min(), data[x_column].max()]
                line_y = [slope * x + intercept for x in line_x]
                
                fig.add_trace(go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', dash='dash')
                ))
            
            fig.update_layout(
                xaxis_title=x_column.replace('_', ' ').title(),
                yaxis_title=y_column.replace('_', ' ').title(),
                hovermode='closest'
            )
            
            # Determine correlation strength
            if abs(correlation) > 0.7:
                strength = "strong"
            elif abs(correlation) > 0.4:
                strength = "moderate"
            else:
                strength = "weak"
            
            direction = "positive" if correlation > 0 else "negative"
            
            return {
                "id": f"scatter_{x_column}_{y_column}",
                "type": "scatter",
                "title": f"{y_column.replace('_', ' ').title()} vs {x_column.replace('_', ' ').title()}",
                "columns": {"x": x_column, "y": y_column, "color": color_column},
                "figure": fig.to_dict(),
                "insights": {
                    "correlation": round(float(correlation), 3),
                    "correlation_strength": strength,
                    "correlation_direction": direction,
                    "interpretation": f"{strength.capitalize()} {direction} relationship"
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "click_action": "filter_other_charts"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating scatter plot: {str(e)}")
            return None
    
    def _generate_histogram_insights(
        self, 
        data: pd.DataFrame,
        column: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate insights for histogram
        """
        return {
            "mean": float(metadata.get('mean', 0)),
            "median": float(metadata.get('median', 0)),
            "std": float(metadata.get('std', 0)),
            "skewness": float(metadata.get('skewness', 0)),
            "distribution": "normal" if abs(metadata.get('skewness', 0)) < 0.5 else "skewed"
        }
    
    def _generate_timeseries_insights(
        self, 
        data: pd.DataFrame,
        time_column: str,
        value_column: str
    ) -> Dict[str, Any]:
        """
        Generate insights for time series
        """
        try:
            return {
                "trend": "increasing" if data[value_column].iloc[-1] > data[value_column].iloc[0] else "decreasing",
                "start_date": str(data[time_column].min()),
                "end_date": str(data[time_column].max()),
                "data_points": len(data)
            }
        except:
            return {}
    
    def create_treemap(
        self,
        data: pd.DataFrame,
        category_column: str,
        value_column: str,
        parent_column: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a treemap for hierarchical data visualization
        """
        try:
            if parent_column:
                # Hierarchical treemap
                fig = px.treemap(
                    data,
                    path=[parent_column, category_column],
                    values=value_column,
                    title=f"{value_column.replace('_', ' ').title()} by {category_column.replace('_', ' ').title()}",
                    template=self.template
                )
            else:
                # Simple treemap
                agg_data = data.groupby(category_column)[value_column].sum().reset_index()
                fig = px.treemap(
                    agg_data,
                    path=[category_column],
                    values=value_column,
                    title=f"{value_column.replace('_', ' ').title()} Distribution",
                    template=self.template
                )
            
            fig.update_traces(textposition='middle center')
            
            return {
                "id": f"treemap_{category_column}_{value_column}",
                "type": "treemap",
                "title": f"{value_column.replace('_', ' ').title()} Treemap",
                "columns": {"category": category_column, "value": value_column, "parent": parent_column},
                "figure": fig.to_dict(),
                "insights": {
                    "largest_segment": str(data.groupby(category_column)[value_column].sum().idxmax()),
                    "total_value": float(data[value_column].sum()),
                    "segments": len(data[category_column].unique())
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "click_action": "drill_down_hierarchy"
                }
            }
        except Exception as e:
            logger.error(f"Error creating treemap: {str(e)}")
            return None
    
    def create_funnel(
        self,
        data: pd.DataFrame,
        stage_column: str,
        value_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a funnel chart for conversion/pipeline analysis
        """
        try:
            # Aggregate by stage
            funnel_data = data.groupby(stage_column)[value_column].sum().reset_index()
            funnel_data = funnel_data.sort_values(value_column, ascending=False)
            
            fig = go.Figure()
            
            fig.add_trace(go.Funnel(
                y=funnel_data[stage_column],
                x=funnel_data[value_column],
                textposition="inside",
                textinfo="value+percent initial",
                marker=dict(color=self.color_scheme[:len(funnel_data)])
            ))
            
            fig.update_layout(
                title=f"{value_column.replace('_', ' ').title()} Funnel",
                template=self.template
            )
            
            # Calculate conversion rates
            conversions = []
            for i in range(len(funnel_data) - 1):
                rate = (funnel_data[value_column].iloc[i+1] / funnel_data[value_column].iloc[i]) * 100
                conversions.append({
                    "from": str(funnel_data[stage_column].iloc[i]),
                    "to": str(funnel_data[stage_column].iloc[i+1]),
                    "rate": round(float(rate), 1)
                })
            
            return {
                "id": f"funnel_{stage_column}_{value_column}",
                "type": "funnel",
                "title": f"{value_column.replace('_', ' ').title()} Funnel",
                "columns": {"stage": stage_column, "value": value_column},
                "figure": fig.to_dict(),
                "insights": {
                    "total_stages": len(funnel_data),
                    "top_stage": str(funnel_data[stage_column].iloc[0]),
                    "bottom_stage": str(funnel_data[stage_column].iloc[-1]),
                    "overall_conversion": round(float((funnel_data[value_column].iloc[-1] / funnel_data[value_column].iloc[0]) * 100), 1),
                    "conversion_rates": conversions
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "click_action": "analyze_stage"
                }
            }
        except Exception as e:
            logger.error(f"Error creating funnel: {str(e)}")
            return None
    
    def create_sankey(
        self,
        data: pd.DataFrame,
        source_column: str,
        target_column: str,
        value_column: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Sankey diagram for flow visualization
        """
        try:
            # Aggregate flows
            if value_column:
                flows = data.groupby([source_column, target_column])[value_column].sum().reset_index()
                flows.columns = ['source', 'target', 'value']
            else:
                flows = data.groupby([source_column, target_column]).size().reset_index(name='value')
                flows.columns = ['source', 'target', 'value']
            
            # Create node labels
            all_nodes = list(set(flows['source'].unique()) | set(flows['target'].unique()))
            node_dict = {node: i for i, node in enumerate(all_nodes)}
            
            # Map to indices
            flows['source_idx'] = flows['source'].map(node_dict)
            flows['target_idx'] = flows['target'].map(node_dict)
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_nodes
                ),
                link=dict(
                    source=flows['source_idx'].tolist(),
                    target=flows['target_idx'].tolist(),
                    value=flows['value'].tolist()
                )
            )])
            
            fig.update_layout(
                title=f"Flow from {source_column.replace('_', ' ').title()} to {target_column.replace('_', ' ').title()}",
                template=self.template,
                font_size=10
            )
            
            return {
                "id": f"sankey_{source_column}_{target_column}",
                "type": "sankey",
                "title": f"Flow Diagram: {source_column} → {target_column}",
                "columns": {"source": source_column, "target": target_column, "value": value_column},
                "figure": fig.to_dict(),
                "insights": {
                    "total_flows": len(flows),
                    "total_nodes": len(all_nodes),
                    "largest_flow": {
                        "from": str(flows.loc[flows['value'].idxmax(), 'source']),
                        "to": str(flows.loc[flows['value'].idxmax(), 'target']),
                        "value": float(flows['value'].max())
                    }
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "click_action": "trace_flow"
                }
            }
        except Exception as e:
            logger.error(f"Error creating sankey: {str(e)}")
            return None
    
    def create_stacked_area(
        self,
        data: pd.DataFrame,
        time_column: str,
        value_column: str,
        category_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a stacked area chart for time series composition
        """
        try:
            # Pivot data for stacking
            pivot_data = data.pivot_table(
                values=value_column,
                index=time_column,
                columns=category_column,
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            fig = go.Figure()
            
            # Add area for each category
            for column in pivot_data.columns[1:]:  # Skip time column
                fig.add_trace(go.Scatter(
                    x=pivot_data[time_column],
                    y=pivot_data[column],
                    mode='lines',
                    name=str(column),
                    stackgroup='one',
                    fillcolor=self.color_scheme[pivot_data.columns[1:].get_loc(column) % len(self.color_scheme)]
                ))
            
            fig.update_layout(
                title=f"{value_column.replace('_', ' ').title()} Over Time by {category_column.replace('_', ' ').title()}",
                xaxis_title="Time",
                yaxis_title=value_column.replace('_', ' ').title(),
                template=self.template,
                hovermode='x unified'
            )
            
            # Calculate insights
            total_by_category = {}
            for column in pivot_data.columns[1:]:
                total_by_category[str(column)] = float(pivot_data[column].sum())
            
            dominant_category = max(total_by_category, key=total_by_category.get)
            
            return {
                "id": f"stacked_area_{time_column}_{value_column}_{category_column}",
                "type": "stacked_area",
                "title": f"{value_column.replace('_', ' ').title()} Composition Over Time",
                "columns": {"time": time_column, "value": value_column, "category": category_column},
                "figure": fig.to_dict(),
                "insights": {
                    "categories": len(pivot_data.columns) - 1,
                    "dominant_category": dominant_category,
                    "dominant_contribution": round(total_by_category[dominant_category] / sum(total_by_category.values()) * 100, 1),
                    "total_by_category": total_by_category
                },
                "interactivity": {
                    "supports_drill_down": True,
                    "cross_filter_enabled": True,
                    "click_action": "filter_category_timeline"
                }
            }
        except Exception as e:
            logger.error(f"Error creating stacked area: {str(e)}")
            return None
