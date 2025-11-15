"""
Data Analysis Routing Agent
Routes user queries to appropriate analysis tools using LLM-based classification.
"""

import json
from typing import Dict, Any, Optional
from groq import Groq
from core.config import get_settings


class RoutingAgent:
    """
    Routes user questions to the correct analysis tool.
    Uses LLM to classify intent and extract parameters.
    """
    
    ROUTING_PROMPT = """You are a Data Analysis Routing Agent.

Your job is to read the user's question and choose EXACTLY ONE tool from the available tools listed below.

You NEVER generate analysis, NEVER calculate values, NEVER write code, and NEVER guess.
You ONLY select the correct tool and fill its arguments.

If the question is vague or missing information, return:
{{
  "needs_clarification": true,
  "message": "Ask user for clarification: ...what is missing..."
}}

Otherwise return:
{{
  "needs_clarification": false,
  "tool": "TOOL_NAME",
  "arguments": {{
      ...parameters needed by the tool...
  }}
}}

-----------------------
TOOLS AVAILABLE
-----------------------

1. SUMMARY  
- Use when the user wants a summary, overview, description, or general insights.
- No arguments.

2. TOP_N  
- Use when the user asks for "top N", "highest N", "bottom N", "lowest N".
Required arguments:
{{
  "column": "<column_name>",
  "n": <number>
}}

3. AVERAGE  
- Use when the user asks for "average", "mean", "typical value".
Required:
{{
  "column": "<column_name>"
}}

4. SUM
- Use when the user asks for "total", "sum", "add up".
Required:
{{
  "column": "<column_name>"
}}

5. FILTER
- Use when the user asks to filter by a value (e.g., "show males", "customers from North").
Required:
{{
  "column": "<column_name>",
  "value": "<filter_value>"
}}

6. COUNT
- Use when the user asks "how many", "count", "number of".
Required:
{{
  "column": "<column_name>",
  "value": "<optional_filter_value>"
}}

7. CHART  
- Use when user wants "plot", "chart", "graph", "visualize".
Required:
{{
  "x_column": "<column_name>",
  "y_column": "<column_name>",
  "chart_type": "<bar|line|scatter|pie>"
}}

8. COMPARE
- Use when user asks to compare two columns or values.
Required:
{{
  "column1": "<column_name>",
  "column2": "<column_name>"
}}

9. FIRST_N or LAST_N
- Use when user asks for "first N rows" or "last N rows".
Required:
{{
  "n": <number>
}}

10. CUSTOM_QUERY
- Use for complex questions that don't fit other tools.
- Sends full question to general LLM agent.
Required:
{{
  "question": "<original_question>"
}}

-----------------------
DATASET COLUMNS
-----------------------
{column_info}

-----------------------
INSTRUCTIONS
-----------------------

- ALWAYS return valid JSON.
- NEVER include comments or explanations.
- NEVER guess missing column names.
- If user does not specify the column, set needs_clarification = true.
- If user asks something unrelated to data, set needs_clarification = true.
- If multiple tools seem possible, choose the MOST specific one.
- Column names must be returned EXACTLY as they appear in the dataset.
- If column name is ambiguous, ask for clarification.

User question: "{question}"

Return only the JSON response:"""

    def __init__(self):
        """Initialize the routing agent."""
        self.settings = get_settings()
        self.groq_client = Groq(api_key=self.settings.groq_api_key) if self.settings.groq_api_key else None
        
    def route(self, question: str, available_columns: list) -> Dict[str, Any]:
        """
        Route a user question to the appropriate tool.
        
        Args:
            question: User's natural language question
            available_columns: List of column names in the dataset
            
        Returns:
            Dictionary with routing decision:
            {
                "needs_clarification": bool,
                "message": str (if needs_clarification),
                "tool": str (if not needs_clarification),
                "arguments": dict (if not needs_clarification)
            }
        """
        if not self.groq_client:
            # Fallback: use custom query for everything
            return {
                "needs_clarification": False,
                "tool": "CUSTOM_QUERY",
                "arguments": {"question": question}
            }
        
        # Prepare column information
        column_info = f"Available columns: {', '.join(available_columns)}"
        
        # Build the routing prompt
        prompt = self.ROUTING_PROMPT.format(
            column_info=column_info,
            question=question
        )
        
        try:
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise routing agent. You ONLY return valid JSON. No explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0,  # Deterministic routing
                max_tokens=300
            )
            
            # Parse the response
            routing_result = response.choices[0].message.content.strip()
            
            # Clean up markdown code blocks if present
            if routing_result.startswith("```"):
                routing_result = routing_result.split("```")[1]
                if routing_result.startswith("json"):
                    routing_result = routing_result[4:]
                routing_result = routing_result.strip()
            
            result = json.loads(routing_result)
            
            return result
            
        except Exception as e:
            print(f"Routing failed: {e}, using CUSTOM_QUERY fallback")
            return {
                "needs_clarification": False,
                "tool": "CUSTOM_QUERY",
                "arguments": {"question": question}
            }
    
    def execute_tool(self, tool: str, arguments: Dict[str, Any], query_engine) -> Dict[str, Any]:
        """
        Execute the selected tool using the query engine.
        
        Args:
            tool: Name of the tool to execute
            arguments: Arguments for the tool
            query_engine: QueryEngine instance to use for execution
            
        Returns:
            Result from the tool execution
        """
        # Map tools to query engine methods
        tool_handlers = {
            "SUMMARY": lambda: query_engine.query("Give me a summary of the dataset"),
            "TOP_N": lambda: query_engine.query(f"Show me the top {arguments.get('n', 10)} {arguments['column']}"),
            "AVERAGE": lambda: query_engine.query(f"What is the average {arguments['column']}?"),
            "SUM": lambda: query_engine.query(f"What is the total {arguments['column']}?"),
            "FILTER": lambda: query_engine.query(f"Show me records where {arguments['column']} is {arguments['value']}"),
            "COUNT": lambda: query_engine.query(f"How many {arguments.get('value', '')} {arguments['column']}?"),
            "CHART": lambda: self._handle_chart(arguments, query_engine),
            "COMPARE": lambda: query_engine.query(f"Compare {arguments['column1']} and {arguments['column2']}"),
            "FIRST_N": lambda: query_engine.query(f"Show me the first {arguments['n']} rows"),
            "LAST_N": lambda: query_engine.query(f"Show me the last {arguments['n']} rows"),
            "CUSTOM_QUERY": lambda: query_engine.query(arguments['question'])
        }
        
        handler = tool_handlers.get(tool)
        if handler:
            return handler()
        else:
            return {
                "success": False,
                "answer": f"Unknown tool: {tool}",
                "query_type": "error"
            }
    
    def _handle_chart(self, arguments: Dict[str, Any], query_engine) -> Dict[str, Any]:
        """Special handler for chart requests."""
        x_col = arguments.get('x_column', '')
        y_col = arguments.get('y_column', '')
        chart_type = arguments.get('chart_type', 'bar')
        
        return {
            "success": True,
            "answer": f"Creating {chart_type} chart with x={x_col}, y={y_col}",
            "query_type": "visualization",
            "visualization_suggestion": {
                "type": chart_type,
                "x": x_col,
                "y": y_col
            }
        }
