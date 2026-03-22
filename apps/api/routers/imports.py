from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from application.dto.import_job import ImportJobRead, ImportStatementResult
from application.services.import_app_service import ImportAppService
from apps.api.dependencies import get_import_service

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/statements", response_model=ImportStatementResult)
async def import_statement(
    household_id: str = Form(...),
    account_id: str = Form(...),
    file: UploadFile = File(...),
    service: ImportAppService = Depends(get_import_service),
) -> ImportStatementResult:
    return service.import_statement(
        household_id=household_id,
        account_id=account_id,
        filename=file.filename or "statement.csv",
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=await file.read(),
    )


@router.get("/jobs/{job_id}", response_model=ImportJobRead)
def get_import_job(
    job_id: str,
    service: ImportAppService = Depends(get_import_service),
) -> ImportJobRead:
    return ImportJobRead.model_validate(service.get_import_job(job_id))

