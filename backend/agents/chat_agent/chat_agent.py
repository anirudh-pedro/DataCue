"""
Chat Agent
Handles natural language questions about datasets
Converts questions to safe read-only queries, validates, and executes
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
import pandas as pd

from .query_validator import QueryValidator
from .result_detector import ResultTypeDetector

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    Chat with CSV functionality:
    1. Receives natural language question + dataset schema
    2. Sends to LLM to get read-only pandas query
    3. Validates query is safe (no writes/deletes)
    4. Executes query on dataset
    5. Detects result type (KPI, table, chart)
    6. Returns formatted result with insight
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.validator = QueryValidator()
        self.result_detector = ResultTypeDetector()
    
    def ask(
        self, 
        question: str,
        metadata: Dict[str, Any],
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Answer a natural language question about the data
        
        Args:
            question: User's natural language question
            metadata: Column names and types
            data: Dataset records
            
        Returns:
            Answer with result data and optional insight
        """
        try:
            # Step 1: Get query from LLM
            query_result = self._generate_query(question, metadata)
            
            if not query_result.get("success"):
                return {
                    "status": "error",
                    "message": query_result.get("error", "Failed to generate query"),
                    "result": None
                }
            
            query_code = query_result["query"]
            
            # Step 2: Validate query is safe (blocks DELETE, UPDATE, DROP, etc.)
            validation = self.validator.validate(query_code)
            if not validation["valid"]:
                return {
                    "status": "error",
                    "message": f"Query rejected: {validation['reason']}",
                    "result": None,
                    "result_type": None
                }
            
            # Step 3: Execute query
            df = pd.DataFrame(data)
            exec_result = self._execute_query(query_code, df)
            
            if exec_result.get("error"):
                return {
                    "status": "error",
                    "message": exec_result["error"],
                    "result": None,
                    "result_type": None
                }
            
            # Step 4: Detect result type and format for frontend
            detected = self.result_detector.detect(
                result=exec_result["raw_result"],
                query=query_code,
                metadata=metadata
            )
            
            # Step 5: Format response for frontend
            return {
                "status": "success",
                "question": question,
                "result": detected["data"],
                "result_type": detected["type"],
                "chart_config": detected.get("config", {}),
                "insight": query_result.get("insight", ""),
                "query_used": query_code,
                "query_type": validation.get("query_type")
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "result": None
            }
    
    def _generate_query(self, question: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pandas query from natural language"""
        
        columns_info = []
        for col in metadata.get("columns", []):
            columns_info.append(f"- {col['name']} ({col['type']})")
        
        prompt = f"""You are a data analyst. Convert this question into a pandas query.

Question: {question}

Dataset columns:
{chr(10).join(columns_info)}
Row count: {metadata.get('row_count', 'unknown')}

Rules:
1. Use ONLY these exact column names
2. Output ONLY a pandas operation that returns data
3. The DataFrame is called 'df'
4. NO assignments, NO print statements
5. Return expressions like: df.groupby('col').sum() or df['col'].mean()
6. For aggregations, use .reset_index() to get a proper DataFrame

Respond with ONLY valid JSON:
{{
  "query": "df.groupby('category')['value'].sum().reset_index()",
  "insight": "Brief explanation of what this shows"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a pandas expert. Respond only with valid JSON containing the query."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "query": result.get("query", ""),
                    "insight": result.get("insight", "")
                }
            
            return {"success": False, "error": "Could not parse LLM response"}
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_query(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute the pandas query safely and return raw result"""
        try:
            # Create a restricted namespace - only allow df and pd
            namespace = {
                'df': df,
                'pd': pd
            }
            
            # Execute query with restricted builtins
            result = eval(query, {"__builtins__": {}}, namespace)
            
            return {
                "raw_result": result,
                "error": None
            }
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "raw_result": None,
                "error": f"Query execution failed: {str(e)}"
            }
