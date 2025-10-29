"""Router exposing single-click orchestration flows."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from services.orchestrator_service import OrchestratorService
from services.knowledge_service import get_shared_service
from services.chat_service import ChatService, get_chat_service
from shared.auth import AuthenticatedUser, authenticate_request, get_authenticated_user
from shared.utils import clean_response

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])
# Inject shared KnowledgeService singleton to ensure /knowledge/ask can answer after pipeline analysis
service = OrchestratorService(knowledge=get_shared_service())

_SESSION_STORE: Dict[str, Dict[str, Any]] = {}
_SESSION_LOCK = asyncio.Lock()


def _ensure_session_owner(
    session_id: Optional[str],
    user: AuthenticatedUser,
    chat_service: ChatService,
) -> None:
    if not session_id:
        return

    session = chat_service.get_session(session_id)
    if not session or session.get("user_id") != user.uid:
        raise HTTPException(status_code=404, detail="Chat session not found")


@router.post("/pipeline")
async def run_pipeline(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    sheet_name: Optional[str] = Form(default=None),
    target_column: Optional[str] = Form(default=None, description="Column to use as prediction target"),
    dashboard_type: str = Form(default="auto"),
    include_advanced_charts: bool = Form(default=True),
    generate_dashboard_insights: bool = Form(default=True),
    knowledge_generate_insights: bool = Form(default=False),
    knowledge_generate_recommendations: bool = Form(default=False),
    prediction_options_json: Optional[str] = Form(default=None, description="JSON object with extra prediction options"),
    chat_session_id: Optional[str] = Form(default=None, description="Associated chat session identifier"),
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        contents = await file.read()
        prediction_options: Optional[Dict[str, Any]] = None
        if prediction_options_json:
            try:
                prediction_options = json.loads(prediction_options_json)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=400, detail=f"Invalid prediction options JSON: {exc}") from exc

        dashboard_options = {
            "dashboard_type": dashboard_type,
            "include_advanced_charts": include_advanced_charts,
            "generate_insights": generate_dashboard_insights,
        }
        knowledge_options = {
            "generate_insights": knowledge_generate_insights,
            "generate_recommendations": knowledge_generate_recommendations,
        }

        _ensure_session_owner(chat_session_id, current_user, chat_service)

        result = service.run_pipeline(
            filename=file.filename or "dataset.csv",
            content=contents,
            sheet_name=sheet_name,
            target_column=target_column,
            dashboard_options=dashboard_options,
            knowledge_options=knowledge_options,
            prediction_options=prediction_options,
            session_id=chat_session_id,
        )
        return clean_response(result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/pipeline/session")
async def create_pipeline_session(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    sheet_name: Optional[str] = Form(default=None),
    target_column: Optional[str] = Form(default=None, description="Column to use as prediction target"),
    dashboard_type: str = Form(default="auto"),
    include_advanced_charts: bool = Form(default=True),
    generate_dashboard_insights: bool = Form(default=True),
    knowledge_generate_insights: bool = Form(default=False),
    knowledge_generate_recommendations: bool = Form(default=False),
    prediction_options_json: Optional[str] = Form(default=None, description="JSON object with extra prediction options"),
    chat_session_id: Optional[str] = Form(default=None, description="Associated chat session identifier"),
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    contents = await file.read()

    prediction_options: Optional[Dict[str, Any]] = None
    if prediction_options_json:
        try:
            prediction_options = json.loads(prediction_options_json)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail=f"Invalid prediction options JSON: {exc}") from exc

    session_id = uuid4().hex
    _ensure_session_owner(chat_session_id, current_user, chat_service)

    session_payload = {
        "filename": file.filename or "dataset.csv",
        "content": contents,
        "sheet_name": sheet_name,
        "target_column": target_column,
        "dashboard_options": {
            "dashboard_type": dashboard_type,
            "include_advanced_charts": include_advanced_charts,
            "generate_insights": generate_dashboard_insights,
        },
        "knowledge_options": {
            "generate_insights": knowledge_generate_insights,
            "generate_recommendations": knowledge_generate_recommendations,
        },
        "prediction_options": prediction_options,
        "chat_session_id": chat_session_id,
        "user_id": current_user.uid,
    }

    async with _SESSION_LOCK:
        _SESSION_STORE[session_id] = session_payload

    return {"session_id": session_id}


@router.get("/pipeline/session/{session_id}/stream")
async def stream_pipeline(
    session_id: str,
    access_token: Optional[str] = Query(default=None, alias="access_token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    debug_user_id: Optional[str] = Header(default=None, alias="X-Debug-User", convert_underscores=False),
):
    user = authenticate_request(authorization=authorization, token=access_token, debug_user_id=debug_user_id)

    async with _SESSION_LOCK:
        session = _SESSION_STORE.pop(session_id, None)

    if not session:
        raise HTTPException(status_code=404, detail="Pipeline session not found or already consumed.")

    if session.get("user_id") != user.uid:
        raise HTTPException(status_code=404, detail="Pipeline session not found or already consumed.")

    queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def status_callback(stage: str, payload: Optional[Dict[str, Any]]) -> None:
        if isinstance(payload, dict):
            try:
                message_payload: Any = clean_response(payload)
            except Exception:  # pragma: no cover - defensive
                message_payload = payload
        else:
            message_payload = payload

        loop.call_soon_threadsafe(
            queue.put_nowait,
            {"stage": stage, "payload": message_payload},
        )

    async def runner() -> None:
        try:
            result = await asyncio.to_thread(
                service.run_pipeline,
                filename=session["filename"],
                content=session["content"],
                sheet_name=session["sheet_name"],
                target_column=session["target_column"],
                dashboard_options=session["dashboard_options"],
                knowledge_options=session["knowledge_options"],
                prediction_options=session["prediction_options"],
                session_id=session.get("chat_session_id"),
                status_callback=status_callback,
            )
            await queue.put({"stage": "pipeline_complete", "payload": clean_response(result)})
        except Exception as exc:  # pragma: no cover - defensive
            await queue.put({"stage": "error", "payload": {"message": str(exc)}})
        finally:
            await queue.put(None)

    asyncio.create_task(runner())

    async def event_generator():
        try:
            while True:
                message = await queue.get()
                if message is None:
                    break
                data = json.dumps(message)
                yield f"data: {data}\n\n"
        finally:
            yield "event: end\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
