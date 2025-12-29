"""FastAPI router for ingestion workflows."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from core.auth import get_current_user, UserInfo
from services.ingestion_service import IngestionService
from shared import storage
from shared.utils import clean_response

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
service = IngestionService()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    sheet_name: str | None = Form(default=None),
    session_id: str | None = Form(default=None, description="Optional session ID for MongoDB storage"),
    current_user: UserInfo = Depends(get_current_user)
):
    try:
        contents = await file.read()
        result = service.ingest_file(
            filename=file.filename,
            content=contents,
            sheet_name=sheet_name,
            session_id=session_id,
            user_id=current_user.uid
        )
        return clean_response(result)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/datasets")
def list_datasets():
    datasets = [path.stem for path in storage.DATA_DIR.glob("*.csv")]
    return {"datasets": datasets, "total": len(datasets)}
