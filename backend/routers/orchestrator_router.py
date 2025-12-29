"""Orchestrator Router - Combined pipeline for file upload + dashboard generation."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from typing import Optional
import uuid
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.auth import get_current_user, FirebaseUser
from services.ingestion_service import IngestionService
from services.dashboard_service import DashboardService
from shared.utils import clean_response

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

ingestion_service = IngestionService()
dashboard_service = DashboardService()

# Store pending pipeline data for streaming
_pipeline_store = {}
_executor = ThreadPoolExecutor(max_workers=4)


@router.post("/pipeline/session")
async def run_pipeline_session(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    dashboard_type: str = Form(default="auto"),
    include_advanced_charts: str = Form(default="false"),
    generate_dashboard_insights: str = Form(default="true"),
    knowledge_generate_insights: str = Form(default="true"),
    knowledge_generate_recommendations: str = Form(default="true"),
    chat_session_id: Optional[str] = Form(default=None),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Start a pipeline session for file upload + dashboard generation.
    Returns session_id immediately, actual processing happens via SSE stream.
    """
    try:
        # Generate pipeline session ID
        pipeline_session_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        session_id = chat_session_id or f"session_{uuid.uuid4().hex[:12]}"
        
        # Read file contents
        contents = await file.read()
        
        # Store pipeline data for processing
        _pipeline_store[pipeline_session_id] = {
            "status": "pending",
            "session_id": session_id,
            "user_id": current_user.uid,
            "filename": file.filename,
            "contents": contents,
            "dashboard_type": dashboard_type,
            "events": [],
            "result": None,
            "error": None,
        }
        
        return {"session_id": pipeline_session_id}
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipeline/session/{pipeline_session_id}/stream")
async def stream_pipeline(pipeline_session_id: str):
    """
    SSE endpoint for streaming pipeline progress.
    """
    if pipeline_session_id not in _pipeline_store:
        raise HTTPException(status_code=404, detail="Pipeline session not found")
    
    async def event_generator():
        pipeline = _pipeline_store[pipeline_session_id]
        session_id = pipeline["session_id"]
        user_id = pipeline["user_id"]
        filename = pipeline["filename"]
        contents = pipeline["contents"]
        dashboard_type = pipeline["dashboard_type"]
        
        try:
            # Stage 1: Upload received
            yield f"data: {json.dumps({'stage': 'upload_received'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Stage 2: Reading CSV
            yield f"data: {json.dumps({'stage': 'reading_csv'})}\n\n"
            
            # Run ingestion in executor to avoid blocking
            loop = asyncio.get_event_loop()
            ingestion_result = await loop.run_in_executor(
                _executor,
                lambda: ingestion_service.ingest_file(
                    filename=filename,
                    content=contents,
                    session_id=session_id,
                    user_id=user_id
                )
            )
            
            if ingestion_result.get("status") == "error":
                error_msg = ingestion_result.get("message", "Ingestion failed")
                yield f"data: {json.dumps({'stage': 'ingestion_failed', 'payload': {'message': error_msg}})}\n\n"
                return
            
            # Stage 3: Ingestion complete
            yield f"data: {json.dumps({'stage': 'ingestion_complete'})}\n\n"
            await asyncio.sleep(0.1)
            
            dataset_id = ingestion_result.get("dataset_id")
            metadata = ingestion_result.get("metadata", {})
            
            # Stage 4: Generating summary
            yield f"data: {json.dumps({'stage': 'generating_summary'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Stage 5: Computing insights
            yield f"data: {json.dumps({'stage': 'computing_insights'})}\n\n"
            
            # Run dashboard generation in executor
            dashboard_result = await loop.run_in_executor(
                _executor,
                lambda: dashboard_service.generate(
                    session_id=session_id,
                    dataset_id=dataset_id,
                    metadata=metadata,
                    user_prompt=f"Generate a {dashboard_type} dashboard with insights"
                )
            )
            
            # Stage 6: Insights ready
            yield f"data: {json.dumps({'stage': 'insights_ready'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Build final payload
            final_payload = {
                "session_id": session_id,
                "dataset_id": dataset_id,
                "dataset_name": filename,
                "steps": {
                    "ingestion": {
                        "rows_parsed": ingestion_result.get("rows_parsed", 0),
                        "columns_parsed": ingestion_result.get("columns_parsed", 0),
                        "dataset_id": dataset_id,
                    },
                    "dashboard": {
                        "charts": dashboard_result.get("dashboard", {}).get("charts", []),
                        "insights": dashboard_result.get("insights", []),
                    }
                }
            }
            
            # Stage 7: Pipeline complete
            yield f"data: {json.dumps({'stage': 'pipeline_complete', 'payload': final_payload})}\n\n"
            
            # Cleanup
            if pipeline_session_id in _pipeline_store:
                del _pipeline_store[pipeline_session_id]
                
        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'payload': {'message': str(e)}})}\n\n"
            if pipeline_session_id in _pipeline_store:
                del _pipeline_store[pipeline_session_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
def orchestrator_health():
    """Health check for orchestrator service"""
    return {"status": "ok", "service": "orchestrator"}
