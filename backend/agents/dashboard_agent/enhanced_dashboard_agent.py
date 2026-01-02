"""
Enhanced Dashboard Agent with SQL-Based Chart Generation
Each chart makes individual LLM request(s) to generate PostgreSQL queries
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
import pandas as pd
from sqlalchemy import text

from core.database import get_db
from .structured_prompts import (
    SYSTEM_PROMPT_PLANNER,
    SYSTEM_PROMPT_SQL,
    SYSTEM_PROMPT_INSIGHTS,
    build_dashboard_planner_prompt,
    build_chart_sql_prompt,
    build_insights_prompt,
    validate_sql_safety,
    extract_json_from_response
)

logger = logging.getLogger(__name__)


class EnhancedDashboardAgent:
    """
    Production-grade dashboard generation using SQL-based approach
    
    Pipeline:
    1. Dashboard Planning: 1 LLM request → Generate 6-10 chart specifications
    2. SQL Generation: 10+ LLM requests → One per chart (or more if multiple queries needed)
    3. Query Execution: Run generated SQL against PostgreSQL
    4. Chart Building: Convert SQL results to Plotly figures
    5. Insights Generation: 1 LLM request → Extract key insights
    
    Total LLM requests: 12-22+ (1 planning + 6-10+ per chart + 1 insights)
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.max_charts = 12
        self.min_charts = 6
        
    def generate_dashboard(
        self,
        metadata: Dict[str, Any],
        session_id: str,
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete dashboard using SQL-based pipeline
        
        Args:
            metadata: Dataset schema with columns and types
            session_id: Session identifier for database access
            user_prompt: Optional user guidance
            
        Returns:
            Complete dashboard configuration with charts and insights
        """
        try:
            logger.info("Starting SQL-based dashboard generation pipeline")
            
            # STEP 1: Dashboard Planning (1 LLM request)
            logger.info("Step 1: Planning dashboard structure (LLM Request #1)")
            dashboard_plan = self._plan_dashboard(metadata, user_prompt)
            
            if not dashboard_plan or "charts" not in dashboard_plan:
                raise ValueError("Failed to generate dashboard plan")
            
            num_charts = len(dashboard_plan['charts'])
            logger.info(f"Generated plan with {num_charts} charts")
            
            # STEP 2: Generate SQL and build charts (1 LLM request per chart)
            logger.info(f"Step 2: Generating SQL queries for {num_charts} charts")
            charts = []
            llm_request_count = 1  # Already made 1 for planning
            
            for idx, chart_spec in enumerate(dashboard_plan["charts"], start=1):
                try:
                    logger.info(f"Processing chart {idx}/{num_charts}: {chart_spec.get('title')}")
                    
                    # Make individual LLM request for this chart's SQL
                    chart = self._build_chart_with_sql(
                        chart_spec,
                        metadata,
                        session_id,
                        llm_request_count + idx
                    )
                    
                    if chart:
                        charts.append(chart)
                        logger.info(f"✓ Chart {idx} built successfully")
                    else:
                        logger.warning(f"✗ Chart {idx} build failed")
                        
                except Exception as e:
                    logger.warning(f"Failed to build chart '{chart_spec.get('title')}': {e}")
                    continue
            
            llm_request_count += num_charts
            logger.info(f"Successfully built {len(charts)} charts ({llm_request_count} LLM requests so far)")
            
            # STEP 3: Generate insights (1 final LLM request)
            logger.info(f"Step 3: Generating insights (LLM Request #{llm_request_count + 1})")
            insights = self._generate_insights(metadata, charts, None)
            
            # Build final dashboard
            dashboard_id = f"dashboard_{uuid.uuid4().hex[:8]}"
            dashboard_config = {
                "dashboard_id": dashboard_id,
                "title": dashboard_plan.get("dashboard_title", "Analytics Dashboard"),
                "description": f"Professional analytics with {len(charts)} visualizations",
                "charts": charts
            }
            
            logger.info(f"✓ Dashboard complete! Total LLM requests: {llm_request_count + 1}")
            
            return {
                "status": "success",
                "dashboard": dashboard_config,
                "insights": insights,
                "stats": {
                    "total_charts": len(charts),
                    "llm_requests": llm_request_count + 1
                }
            }
            
        except Exception as e:
            logger.error(f"Dashboard generation error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "dashboard": None
            }
    
    def _plan_dashboard(self, metadata: Dict[str, Any], user_prompt: Optional[str]) -> Dict[str, Any]:
        """
        Step 1: Use LLM to plan dashboard structure
        
        Returns:
            Dashboard plan with chart specifications
        """
        try:
            prompt = build_dashboard_planner_prompt(metadata)
            
            if user_prompt:
                prompt += f"\n\nUSER REQUEST:\n{user_prompt}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_PLANNER},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Dashboard plan response: {response_text[:200]}...")
            
            # Extract JSON from response
            dashboard_plan = extract_json_from_response(response_text)
            
            # Validate plan structure
            if not isinstance(dashboard_plan, dict) or "charts" not in dashboard_plan:
                raise ValueError("Invalid dashboard plan structure")
            
            # Limit charts to max
            if len(dashboard_plan["charts"]) > self.max_charts:
                dashboard_plan["charts"] = dashboard_plan["charts"][:self.max_charts]
            
            return dashboard_plan
            
        except Exception as e:
            logger.warning(f"Dashboard planning failed: {e}, using fallback")
            return self._fallback_dashboard_plan(metadata)
    
    def _build_chart_with_sql(
        self,
        chart_spec: Dict[str, Any],
        metadata: Dict[str, Any],
        session_id: str,
        request_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Build a chart by making individual LLM request(s) to generate SQL query/queries
        
        This is the core method that makes 1+ LLM requests per chart
        
        Args:
            chart_spec: Chart specification from planning phase
            metadata: Dataset metadata
            session_id: Session identifier
            request_number: Current LLM request number (for logging)
            
        Returns:
            Complete chart object with Plotly figure, or None if failed
        """
        try:
            chart_title = chart_spec.get('title', 'Untitled Chart')
            queries_needed = chart_spec.get('queries_needed', 1)
            
            logger.info(f"  LLM Request #{request_number}: Generating {queries_needed} SQL query/queries for '{chart_title}'")
            
            # Build prompt for SQL generation
            sql_prompt = build_chart_sql_prompt(metadata, chart_spec)
            
            # Make LLM request to generate SQL
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_SQL},
                    {"role": "user", "content": sql_prompt}
                ],
                temperature=0.1,  # Low temperature for precise SQL
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"  SQL Response: {response_text[:150]}...")
            
            # Parse SQL queries from response
            if queries_needed == 1:
                # Single query expected
                sql_queries = [self._extract_sql_query(response_text)]
            else:
                # Multiple queries expected (JSON array)
                try:
                    sql_queries = extract_json_from_response(response_text)
                    if not isinstance(sql_queries, list):
                        sql_queries = [response_text]
                except:
                    sql_queries = [response_text]
            
            # Validate SQL safety
            for sql in sql_queries:
                safety = validate_sql_safety(sql)
                if not safety["safe"]:
                    logger.warning(f"  ✗ Unsafe SQL detected: {safety['reason']}")
                    return None
            
            logger.info(f"  ✓ Generated {len(sql_queries)} safe SQL query/queries")
            
            # Execute SQL queries against PostgreSQL
            query_results = []
            db = next(get_db())
            
            try:
                for idx, sql in enumerate(sql_queries, 1):
                    logger.debug(f"  Executing query {idx}: {sql[:100]}...")
                    
                    # Replace table name with actual uploaded_data reference
                    # In PostgreSQL, we store data in dataset_rows table with JSONB
                    # Need to construct proper query for JSONB data
                    result = self._execute_sql_on_session_data(db, session_id, sql)
                    
                    if result is not None:
                        query_results.append(result)
                        logger.debug(f"  ✓ Query {idx} returned {len(result)} rows")
                    else:
                        logger.warning(f"  ✗ Query {idx} returned no results")
                
            finally:
                db.close()
            
            if not query_results:
                logger.warning(f"  ✗ No query results for chart '{chart_title}'")
                return None
            
            # Convert SQL results to Plotly figure
            figure = self._sql_results_to_plotly(
                chart_spec,
                query_results
            )
            
            if not figure:
                logger.warning(f"  ✗ Failed to create Plotly figure for '{chart_title}'")
                return None
            
            # Build final chart object
            return {
                "id": chart_spec.get("chart_id", f"chart_{uuid.uuid4().hex[:6]}"),
                "chart_id": chart_spec.get("chart_id"),
                "type": chart_spec.get("chart_type"),
                "title": chart_title,
                "description": chart_spec.get("description", ""),
                "figure": figure,
                "priority": chart_spec.get("priority", 5),
                "queries": sql_queries  # Include queries for debugging
            }
            
        except Exception as e:
            logger.error(f"Failed to build chart with SQL: {e}", exc_info=True)
            return None
    
    def _extract_sql_query(self, text: str) -> str:
        """Extract SQL query from LLM response, handling markdown code blocks"""
        # Remove markdown code blocks if present
        if "```sql" in text:
            text = text.split("```sql")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return text.strip()
    
    def _execute_sql_on_session_data(
        self,
        db,
        session_id: str,
        sql_query: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute SQL query on uploaded data stored in PostgreSQL
        
        The uploaded CSV data is stored as JSONB in dataset_rows table
        We need to convert the user's SQL query to work with our JSONB structure
        
        Args:
            db: Database session
            session_id: Session identifier
            sql_query: SQL query from LLM (references 'uploaded_data' table)
            
        Returns:
            List of result dictionaries, or None if failed
        """
        try:
            # Strategy: Load the session's data into memory as DataFrame
            # Then use pandas to execute the query logic
            # (More reliable than trying to convert SQL to JSONB queries)
            
            from core.models import DatasetRow
            
            # Fetch all rows for this session
            rows = db.query(DatasetRow).filter(
                DatasetRow.session_id == session_id
            ).all()
            
            if not rows:
                logger.warning(f"No data found for session {session_id}")
                return None
            
            # Convert to DataFrame
            data = [row.data for row in rows]
            df = pd.DataFrame(data)
            
            logger.debug(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
            
            # Execute SQL using pandas SQL capabilities
            # Replace 'uploaded_data' with actual DataFrame name
            sql_for_pandas = sql_query.replace("uploaded_data", "df")
            sql_for_pandas = sql_for_pandas.replace("FROM df", "")
            sql_for_pandas = sql_for_pandas.replace("from df", "")
            
            # Use pandasql or execute directly via pandas operations
            # For simplicity, we'll parse and execute common patterns
            result_df = self._execute_sql_with_pandas(df, sql_query)
            
            if result_df is None or result_df.empty:
                return None
            
            # Convert to list of dicts
            return result_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}", exc_info=True)
            return None
    
    def _execute_sql_with_pandas(
        self,
        df: pd.DataFrame,
        sql: str
    ) -> Optional[pd.DataFrame]:
        """
        Execute SQL query using pandas operations
        
        Supports common SQL patterns:
        - SELECT col1, col2 FROM table
        - SELECT col, COUNT(*) FROM table GROUP BY col
        - SELECT col, AVG(metric) FROM table GROUP BY col
        - SELECT * FROM table WHERE condition
        - SELECT * FROM table LIMIT n
        """
        try:
            sql_upper = sql.upper()
            
            # Extract SELECT clause
            select_part = sql[sql_upper.find("SELECT") + 6:sql_upper.find("FROM")].strip()
            
            # Check for GROUP BY
            if "GROUP BY" in sql_upper:
                group_by_start = sql_upper.find("GROUP BY") + 8
                group_by_end = sql_upper.find("ORDER BY") if "ORDER BY" in sql_upper else sql_upper.find("LIMIT") if "LIMIT" in sql_upper else len(sql)
                group_by_cols = sql[group_by_start:group_by_end].strip().split(",")
                group_by_cols = [col.strip() for col in group_by_cols]
                
                # Parse aggregations
                result = self._execute_group_by(df, select_part, group_by_cols)
            else:
                # Simple SELECT
                if select_part == "*":
                    result = df.copy()
                else:
                    cols = [c.strip() for c in select_part.split(",")]
                    result = df[cols].copy()
            
            # Handle LIMIT
            if "LIMIT" in sql_upper:
                limit_start = sql_upper.find("LIMIT") + 5
                limit_num = int(sql[limit_start:].strip().split()[0])
                result = result.head(limit_num)
            
            return result
            
        except Exception as e:
            logger.error(f"Pandas SQL execution failed: {e}")
            # Fallback: try using pandasql library
            try:
                import pandasql as ps
                result = ps.sqldf(sql.replace("uploaded_data", "df"), locals())
                return result
            except:
                return None
    
    def _execute_group_by(
        self,
        df: pd.DataFrame,
        select_clause: str,
        group_by_cols: List[str]
    ) -> pd.DataFrame:
        """Execute GROUP BY query with aggregations"""
        # Parse select clause for aggregations
        # Examples: "region, COUNT(*)", "department, AVG(salary)", "category, SUM(revenue)"
        
        parts = [p.strip() for p in select_clause.split(",")]
        
        agg_dict = {}
        group_cols = []
        
        for part in parts:
            part_upper = part.upper()
            
            if "COUNT(*)" in part_upper or "COUNT(1)" in part_upper:
                agg_dict['count'] = ('id', 'count') if 'id' in df.columns else (df.columns[0], 'count')
            elif "AVG(" in part_upper:
                col = part[part.find("(") + 1:part.find(")")].strip()
                agg_dict[f'avg_{col}'] = (col, 'mean')
            elif "SUM(" in part_upper:
                col = part[part.find("(") + 1:part.find(")")].strip()
                agg_dict[f'sum_{col}'] = (col, 'sum')
            elif "MIN(" in part_upper:
                col = part[part.find("(") + 1:part.find(")")].strip()
                agg_dict[f'min_{col}'] = (col, 'min')
            elif "MAX(" in part_upper:
                col = part[part.find("(") + 1:part.find(")")].strip()
                agg_dict[f'max_{col}'] = (col, 'max')
            else:
                # Regular column
                group_cols.append(part)
        
        # Perform groupby
        if agg_dict:
            grouped = df.groupby(group_by_cols[0] if len(group_by_cols) == 1 else group_by_cols)
            result = grouped.agg(**{k: v for k, v in agg_dict.items()}).reset_index()
        else:
            result = df[group_cols].drop_duplicates()
        
        return result
    
    def _build_chart_from_spec(
        self,
        chart_spec: Dict[str, Any],
        df: pd.DataFrame,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        LEGACY METHOD - kept for backward compatibility
        Build a chart from specification by generating and executing query
        
        Args:
            chart_spec: Chart specification from planning phase
            df: DataFrame with data
            metadata: Dataset metadata
            
        Returns:
            Complete chart object with Plotly figure
        """
        chart_type = chart_spec.get("chart_type", "bar")
        dimensions = chart_spec.get("dimensions", [])
        metrics = chart_spec.get("metrics", [])
        
        # For DataFrame operations, we'll use pandas directly instead of SQL
        # This is safer and more efficient for in-memory data
        figure = self._build_plotly_figure_from_spec(
            chart_spec,
            df,
            dimensions,
            metrics
        )
        
        if not figure:
            return None
        
        return {
            "id": chart_spec.get("chart_id", f"chart_{uuid.uuid4().hex[:6]}"),
            "chart_id": chart_spec.get("chart_id"),
            "type": chart_type,
            "title": chart_spec.get("title", "Chart"),
            "description": chart_spec.get("description", ""),
            "figure": figure,
            "priority": chart_spec.get("priority", 5)
        }
    
    def _sql_results_to_plotly(
        self,
        chart_spec: Dict[str, Any],
        query_results: List[List[Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Convert SQL query results to Plotly figure
        
        Args:
            chart_spec: Chart specification with type and metadata
            query_results: List of query results (each query returns list of dicts)
            
        Returns:
            Plotly figure dict or None
        """
        try:
            chart_type = chart_spec.get("chart_type", "bar").lower()
            
            # Base layout
            base_layout = {
                "margin": {"t": 40, "r": 20, "b": 80, "l": 60},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
                "font": {"color": "#a0aec0", "size": 12},
                "xaxis": {
                    "gridcolor": "rgba(255, 255, 255, 0.05)",
                    "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                    "color": "#718096"
                },
                "yaxis": {
                    "gridcolor": "rgba(255, 255, 255, 0.05)",
                    "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                    "color": "#718096"
                },
            }
            
            # Convert first query result to DataFrame
            df = pd.DataFrame(query_results[0])
            
            if df.empty:
                return None
            
            # Detect X and Y columns (first two columns typically)
            columns = list(df.columns)
            x_col = columns[0] if len(columns) > 0 else None
            y_col = columns[1] if len(columns) > 1 else columns[0]
            
            # Build chart based on type
            if chart_type == "bar":
                return {
                    "data": [{
                        "type": "bar",
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "marker": {"color": "#805AD5"}
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
            elif chart_type == "line":
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "lines+markers",
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "line": {"color": "#4299E1", "width": 2},
                        "marker": {"size": 6}
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
            elif chart_type == "pie":
                return {
                    "data": [{
                        "type": "pie",
                        "labels": df[x_col].tolist(),
                        "values": df[y_col].tolist(),
                        "marker": {
                            "colors": ["#805AD5", "#4299E1", "#48BB78", "#ED8936", "#F56565"]
                        }
                    }],
                    "layout": {
                        **base_layout,
                        "showlegend": True
                    }
                }
            
            elif chart_type == "scatter":
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "markers",
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "marker": {"size": 8, "color": "#805AD5"}
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
            elif chart_type == "histogram":
                return {
                    "data": [{
                        "type": "histogram",
                        "x": df[x_col].tolist(),
                        "marker": {"color": "#48BB78"}
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": "Count"}
                    }
                }
            
            elif chart_type == "box":
                return {
                    "data": [{
                        "type": "box",
                        "y": df[y_col].tolist(),
                        "name": y_col,
                        "marker": {"color": "#4299E1"}
                    }],
                    "layout": {
                        **base_layout,
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
            elif chart_type == "area":
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "lines",
                        "fill": "tozeroy",
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "line": {"color": "#48BB78"},
                        "fillcolor": "rgba(72, 187, 120, 0.3)"
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
            else:
                # Default to bar chart
                return {
                    "data": [{
                        "type": "bar",
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "marker": {"color": "#805AD5"}
                    }],
                    "layout": {
                        **base_layout,
                        "xaxis": {**base_layout["xaxis"], "title": x_col},
                        "yaxis": {**base_layout["yaxis"], "title": y_col}
                    }
                }
            
        except Exception as e:
            logger.error(f"Failed to convert SQL results to Plotly: {e}", exc_info=True)
            return None
    
    def _build_plotly_figure_from_spec(
        self,
        chart_spec: Dict[str, Any],
        df: pd.DataFrame,
        dimensions: List[str],
        metrics: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Build Plotly figure from chart specification
        
        Args:
            chart_spec: Chart specification
            df: DataFrame with data
            dimensions: Grouping columns
            metrics: Aggregation expressions
            
        Returns:
            Plotly figure dict or None
        """
        chart_type = chart_spec.get("chart_type", "bar").lower()
        
        # Base layout for all charts
        base_layout = {
            "margin": {"t": 40, "r": 20, "b": 80, "l": 60},
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
            "font": {"color": "#a0aec0", "size": 12},
            "xaxis": {
                "gridcolor": "rgba(255, 255, 255, 0.05)",
                "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                "color": "#718096"
            },
            "yaxis": {
                "gridcolor": "rgba(255, 255, 255, 0.05)",
                "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                "color": "#718096"
            },
        }
        
        try:
            # Extract column names from dimensions and metrics
            dim_col = dimensions[0] if dimensions else None
            
            # Parse metric (e.g., "AVG(salary)" -> column="salary", agg="mean")
            if metrics:
                metric_str = metrics[0]
                agg_func, metric_col = self._parse_metric(metric_str)
            else:
                agg_func, metric_col = "count", None
            
            # Validate columns exist
            if dim_col and dim_col not in df.columns:
                logger.warning(f"Dimension column '{dim_col}' not found in data")
                return None
            
            if metric_col and metric_col not in df.columns:
                logger.warning(f"Metric column '{metric_col}' not found in data")
                return None
            
            # Build chart based on type
            if chart_type == "histogram":
                return self._build_histogram(df, dim_col or metric_col, base_layout)
            
            elif chart_type == "pie":
                return self._build_pie_chart(df, dim_col, base_layout)
            
            elif chart_type == "scatter":
                # Need two dimensions for scatter
                x_col = dimensions[0] if len(dimensions) > 0 else None
                y_col = dimensions[1] if len(dimensions) > 1 else metric_col
                return self._build_scatter(df, x_col, y_col, base_layout)
            
            elif chart_type == "line":
                return self._build_line_chart(df, dim_col, metric_col, agg_func, base_layout)
            
            elif chart_type == "area":
                return self._build_area_chart(df, dim_col, metric_col, agg_func, base_layout)
            
            elif chart_type == "box":
                return self._build_box_plot(df, dim_col, metric_col, base_layout)
            
            else:  # Default to bar chart
                return self._build_bar_chart(df, dim_col, metric_col, agg_func, base_layout)
        
        except Exception as e:
            logger.warning(f"Failed to build {chart_type} chart: {e}")
            return None
    
    def _parse_metric(self, metric_str: str) -> tuple:
        """Parse metric string like 'AVG(salary)' into (aggregation, column)"""
        import re
        match = re.match(r'(\w+)\((\w+)\)', metric_str.strip())
        if match:
            agg, col = match.groups()
            agg_map = {
                'AVG': 'mean', 'SUM': 'sum', 'COUNT': 'count',
                'MIN': 'min', 'MAX': 'max', 'MEDIAN': 'median'
            }
            return agg_map.get(agg.upper(), 'sum'), col
        return 'count', metric_str
    
    def _build_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, agg: str, layout: dict) -> dict:
        """Build bar chart"""
        if not x_col or (y_col and y_col not in df.columns):
            return None
        
        if y_col:
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
            grouped = grouped.sort_values(y_col, ascending=False).head(15)
        else:
            grouped = df[x_col].value_counts().head(15).reset_index()
            grouped.columns = [x_col, 'count']
            y_col = 'count'
        
        return {
            "data": [{
                "type": "bar",
                "x": grouped[x_col].tolist(),
                "y": grouped[y_col].tolist(),
                "marker": {"color": "#667eea", "line": {"color": "#764ba2", "width": 1}},
            }],
            "layout": {**layout, "bargap": 0.3}
        }
    
    def _build_histogram(self, df: pd.DataFrame, col: str, layout: dict) -> dict:
        """Build histogram"""
        if not col or col not in df.columns:
            return None
        
        values = df[col].dropna()
        if values.empty:
            return None
        
        return {
            "data": [{
                "type": "histogram",
                "x": values.tolist(),
                "marker": {"color": "#37cdff", "line": {"color": "#667eea", "width": 1}},
                "nbinsx": 30
            }],
            "layout": {**layout, "bargap": 0.05}
        }
    
    def _build_pie_chart(self, df: pd.DataFrame, col: str, layout: dict) -> dict:
        """Build pie chart"""
        if not col or col not in df.columns:
            return None
        
        counts = df[col].value_counts().head(8)
        if counts.empty:
            return None
        
        colors = ['#667eea', '#37cdff', '#38ef7d', '#feb47b', '#fe5196', '#764ba2', '#11998e', '#f77062']
        
        return {
            "data": [{
                "type": "pie",
                "labels": counts.index.tolist(),
                "values": counts.values.tolist(),
                "hole": 0.4,
                "marker": {"colors": colors, "line": {"color": "#0a0e27", "width": 2}},
                "textposition": "inside",
                "textinfo": "percent+label",
            }],
            "layout": {**layout, "showlegend": False}
        }
    
    def _build_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, layout: dict) -> dict:
        """Build scatter plot"""
        if not x_col or not y_col or x_col not in df.columns or y_col not in df.columns:
            return None
        
        scatter_df = df[[x_col, y_col]].dropna()
        if scatter_df.empty:
            return None
        
        return {
            "data": [{
                "type": "scatter",
                "mode": "markers",
                "x": scatter_df[x_col].tolist(),
                "y": scatter_df[y_col].tolist(),
                "marker": {"color": "#38ef7d", "size": 8, "opacity": 0.6},
            }],
            "layout": layout
        }
    
    def _build_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, agg: str, layout: dict) -> dict:
        """Build line chart"""
        if not x_col or not y_col or x_col not in df.columns or y_col not in df.columns:
            return None
        
        grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
        if grouped.empty:
            return None
        
        return {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": grouped[x_col].tolist(),
                "y": grouped[y_col].tolist(),
                "line": {"color": "#667eea", "width": 3},
                "marker": {"color": "#764ba2", "size": 6},
            }],
            "layout": layout
        }
    
    def _build_area_chart(self, df: pd.DataFrame, x_col: str, y_col: str, agg: str, layout: dict) -> dict:
        """Build area chart"""
        if not x_col or not y_col or x_col not in df.columns or y_col not in df.columns:
            return None
        
        grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
        if grouped.empty:
            return None
        
        return {
            "data": [{
                "type": "scatter",
                "mode": "lines",
                "x": grouped[x_col].tolist(),
                "y": grouped[y_col].tolist(),
                "fill": "tozeroy",
                "fillcolor": "rgba(102, 126, 234, 0.3)",
                "line": {"color": "#667eea", "width": 2},
            }],
            "layout": layout
        }
    
    def _build_box_plot(self, df: pd.DataFrame, x_col: str, y_col: str, layout: dict) -> dict:
        """Build box plot"""
        if not y_col or y_col not in df.columns:
            return None
        
        if x_col and x_col in df.columns:
            # Grouped box plot
            categories = df[x_col].unique()[:10]
            data = []
            for cat in categories:
                values = df[df[x_col] == cat][y_col].dropna()
                if not values.empty:
                    data.append({
                        "type": "box",
                        "y": values.tolist(),
                        "name": str(cat),
                        "marker": {"color": "#667eea"}
                    })
            return {"data": data, "layout": layout}
        else:
            # Single box plot
            values = df[y_col].dropna()
            if values.empty:
                return None
            return {
                "data": [{
                    "type": "box",
                    "y": values.tolist(),
                    "marker": {"color": "#667eea"}
                }],
                "layout": layout
            }
    
    def _generate_insights(self, metadata: Dict[str, Any], charts: List[Dict], df: pd.DataFrame) -> List[str]:
        """Generate insights from charts and data"""
        try:
            # Build summary of query results
            query_results = []
            for chart in charts[:3]:  # Limit to first 3 charts
                query_results.append({
                    "title": chart.get("title"),
                    "type": chart.get("type"),
                    "description": chart.get("description")
                })
            
            prompt = build_insights_prompt(metadata, query_results)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_INSIGHTS},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            insights_data = extract_json_from_response(response_text)
            
            return [insight.get("description", insight) for insight in insights_data.get("insights", [])]
        
        except Exception as e:
            logger.warning(f"Insights generation failed: {e}")
            return [
                f"Dashboard contains {len(charts)} visualizations covering key data dimensions.",
                f"Dataset includes {metadata.get('row_count', 0)} records across {metadata.get('column_count', 0)} columns."
            ]
    
    def _fallback_dashboard_plan(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback dashboard plan when LLM fails"""
        columns = metadata.get("columns", [])
        numeric_cols = [c for c in columns if c["type"] in ("numeric", "integer", "float")]
        categorical_cols = [c for c in columns if c["type"] in ("categorical", "string")]
        
        charts = []
        
        # Bar chart
        if categorical_cols and numeric_cols:
            charts.append({
                "chart_id": "chart_1",
                "title": f"{numeric_cols[0]['name'].title()} by {categorical_cols[0]['name'].title()}",
                "chart_type": "bar",
                "description": f"Distribution of {numeric_cols[0]['name']} across {categorical_cols[0]['name']}",
                "dimensions": [categorical_cols[0]['name']],
                "metrics": [f"SUM({numeric_cols[0]['name']})"],
                "queries_needed": 1,
                "priority": 1
            })
        
        # Histogram
        if numeric_cols:
            charts.append({
                "chart_id": "chart_2",
                "title": f"{numeric_cols[0]['name'].title()} Distribution",
                "chart_type": "histogram",
                "description": f"Frequency distribution of {numeric_cols[0]['name']}",
                "dimensions": [numeric_cols[0]['name']],
                "metrics": ["COUNT(*)"],
                "queries_needed": 1,
                "priority": 2
            })
        
        # Pie chart
        if categorical_cols:
            charts.append({
                "chart_id": "chart_3",
                "title": f"{categorical_cols[0]['name'].title()} Breakdown",
                "chart_type": "pie",
                "description": f"Proportion of records by {categorical_cols[0]['name']}",
                "dimensions": [categorical_cols[0]['name']],
                "metrics": ["COUNT(*)"],
                "queries_needed": 1,
                "priority": 3
            })
        
        return {
            "dashboard_title": "Data Overview",
            "charts": charts
        }
