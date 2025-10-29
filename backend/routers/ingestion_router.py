"""FastAPI router for ingestion workflows."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from services.ingestion_service import IngestionService
from shared.auth import AuthenticatedUser, get_authenticated_user
from shared import storage
from shared.utils import clean_response

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
service = IngestionService()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    sheet_name: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        contents = await file.read()
        result = service.ingest_file(filename=file.filename, content=contents, sheet_name=sheet_name)
        return clean_response(result)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/datasets")
def list_datasets(current_user: AuthenticatedUser = Depends(get_authenticated_user)):
    datasets = [path.stem for path in storage.DATA_DIR.glob("*.csv")]
    return {"datasets": datasets, "total": len(datasets)}
