"""Groq-powered natural language to MongoDB query translation service."""
from __future__ import annotations

import json
import logging
import textwrap
from typing import Any, Dict, List, Optional

from bson import json_util
from groq import Groq

from core.config import get_settings
from services.dataset_service import DatasetService, get_dataset_service

LOGGER = logging.getLogger(__name__)


class MongoQueryService:
    """Convert natural language questions into MongoDB aggregation pipelines."""

    def __init__(self, dataset_service: Optional[DatasetService] = None) -> None:
        self._dataset_service = dataset_service or get_dataset_service()
        self._settings = get_settings()
        self._client: Optional[Groq] = None
        
        self._enabled = bool(
            self._dataset_service.is_enabled and self._settings.groq_api_key
        )
        
        if self._enabled:
            self._client = Groq(api_key=self._settings.groq_api_key)
            LOGGER.info("MongoQueryService initialized with Groq")
        else:
            LOGGER.info("MongoQueryService disabled (missing MongoDB or Groq API key)")

    @property
    def is_enabled(self) -> bool:
        """Check if service is properly configured."""
        return self._enabled and self._client is not None

    def ask(self, *, session_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a natural language question about the session's dataset.
        
        Args:
            session_id: Session identifier with stored dataset
            question: Natural language question from user
            
        Returns:
            Dictionary with success status, answer, generated pipeline, and data
        """
        if not self.is_enabled:
            return {
                "success": False,
                "error": "MongoDB-backed querying is not configured. Set MONGO_URI and GROQ_API_KEY."
            }

        # Fetch dataset metadata
        dataset = self._dataset_service.get_session_dataset(session_id)
        if not dataset:
            return {
                "success": False,
                "error": "No dataset found for this session. Please upload a CSV file first."
            }

        try:
            # Build prompt with dataset context
            prompt = self._build_prompt(
                question=question,
                dataset=dataset,
                session_id=session_id
            )
            
            # Get Groq to generate MongoDB pipeline
            plan = self._call_groq(prompt)
            
        except Exception as exc:
            LOGGER.exception("Failed to generate MongoDB pipeline: %s", exc)
            return {
                "success": False,
                "error": f"Could not generate query for this question: {str(exc)}"
            }

        # Validate response structure
        pipeline = plan.get("pipeline")
        if not isinstance(pipeline, list):
            return {
                "success": False,
                "error": "Groq did not return a valid aggregation pipeline."
            }

        # Add security filters to ensure query only accesses session data
        safe_pipeline = self._prepend_security_filters(
            pipeline,
            dataset_id=dataset["dataset_id"],
            session_id=session_id
        )

        try:
            # Execute the pipeline
            results = self._dataset_service.run_pipeline(
                session_id=session_id,
                dataset_id=dataset["dataset_id"],
                pipeline=safe_pipeline,
            )
            
        except Exception as exc:
            LOGGER.exception("Pipeline execution failed for session %s: %s", session_id, exc)
            return {
                "success": False,
                "error": f"Generated query failed to execute: {str(exc)}"
            }

        # Return structured response
        return {
            "success": True,
            "method": "mongo_llm",
            "question": question,
            "answer": plan.get("summary") or plan.get("answer", "Query executed successfully"),
            "pipeline": pipeline,  # User-facing pipeline (without security filters)
            "data": json.loads(json_util.dumps(results)),  # Convert BSON to JSON-serializable
        }

    def _prepend_security_filters(
        self,
        pipeline: List[Dict[str, Any]],
        *,
        dataset_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Add mandatory filters to restrict query to session's dataset."""
        security_match = {
            "$match": {
                "dataset_id": dataset_id,
                "session_id": session_id
            }
        }
        
        # If pipeline already starts with $match, merge conditions
        if pipeline and isinstance(pipeline[0], dict) and "$match" in pipeline[0]:
            merged_conditions = {
                "$and": [
                    security_match["$match"],
                    pipeline[0]["$match"]
                ]
            }
            return [{"$match": merged_conditions}, *pipeline[1:]]
        
        # Otherwise prepend security match
        return [security_match, *pipeline]

    def _call_groq(self, prompt: str) -> Dict[str, Any]:
        """Call Groq API to generate MongoDB aggregation pipeline."""
        response = self._client.chat.completions.create(
            model=self._settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior MongoDB engineer. "
                        "Reply ONLY with valid JSON containing an aggregation pipeline. "
                        "Do not include explanations outside the JSON structure."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
        )
        
        content = response.choices[0].message.content.strip()
        return self._extract_json(content)

    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from Groq response, handling markdown code blocks."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            start = content.find("{")
            end = content.rfind("}")
            
            if start == -1 or end == -1:
                raise ValueError("No JSON object found in Groq response")
            
            json_str = content[start:end + 1]
            return json.loads(json_str)

    def _build_prompt(
        self,
        *,
        question: str,
        dataset: Dict[str, Any],
        session_id: str
    ) -> str:
        """Build comprehensive prompt for Groq with dataset context."""
        column_map = dataset.get("column_map", {})
        metadata = dataset.get("metadata", {})
        
        # Extract column metadata if available
        columns_meta = metadata.get("columns_metadata") if isinstance(metadata, dict) else {}
        
        # Get sample rows for context
        sample_rows = self._dataset_service.get_sample_rows(
            dataset_id=dataset["dataset_id"],
            session_id=session_id,
            limit=5
        )
        
        # Build column information
        columns_info = []
        for original_name, sanitized_name in column_map.items():
            col_info = {
                "original": original_name,
                "field": sanitized_name,
            }
            
            # Add data type if available
            if isinstance(columns_meta, dict) and original_name in columns_meta:
                col_meta = columns_meta[original_name]
                if isinstance(col_meta, dict):
                    col_info["data_type"] = col_meta.get("data_type")
            
            columns_info.append(col_info)
        
        # Build the prompt
        prompt = textwrap.dedent(f"""
            You are analyzing a MongoDB collection named `session_dataset_rows`.
            Each document represents one row from the user's dataset.
            
            Every document has these fields:
            - session_id: Session identifier (string)
            - dataset_id: Dataset identifier (string)  
            - row_index: Row number from original CSV (integer)
            - Plus one field per dataset column (see below)
            
            AVAILABLE COLUMNS (use the "field" name in your queries, NOT "original"):
            {json.dumps(columns_info, indent=2)}
            
            CRITICAL: Always use the sanitized "field" names in your pipeline, never the "original" column names.
            
            SAMPLE DOCUMENTS from this dataset:
            {json.dumps(sample_rows, indent=2)}
            
            DATASET INFO:
            - Name: {dataset.get('dataset_name')}
            - Total rows: {dataset.get('row_count')}
            - Session: {session_id}
            
            USER QUESTION: {question}
            
            Generate a MongoDB aggregation pipeline to answer this question.
            Return your response as STRICT JSON with this exact structure:
            {{
              "pipeline": [
                // Array of MongoDB aggregation stages
                // Use $match, $group, $project, $sort, $limit, etc.
              ],
              "summary": "One sentence explaining what the results show"
            }}
            
            CONSTRAINTS:
            1. Use ONLY the sanitized field names listed above
            2. Do NOT add $match stages for session_id/dataset_id (handled automatically)
            3. NEVER use: $out, $merge, $function, $accumulator, $where, or server-side JS
            4. For text filtering, use case-insensitive regex: {{"$regex": "pattern", "$options": "i"}}
            5. When returning raw documents, limit to 50 rows maximum
            6. For numeric comparisons on string fields, cast using $toDouble or $toInt
            7. For counting, use {{"$count": "count"}} or {{"$group": {{"_id": null, "count": {{"$sum": 1}}}}}}
            8. Be concise and precise
            
            Return ONLY valid JSON, no additional text.
        """).strip()
        
        return prompt


_MONGO_QUERY_SERVICE: Optional[MongoQueryService] = None


def get_mongo_query_service() -> MongoQueryService:
    """Get or create singleton MongoQueryService instance."""
    global _MONGO_QUERY_SERVICE
    if _MONGO_QUERY_SERVICE is None:
        _MONGO_QUERY_SERVICE = MongoQueryService()
    return _MONGO_QUERY_SERVICE
