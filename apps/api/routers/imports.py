from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from application.dto.import_job import ImportJobRead, ImportStatementResult
from application.services.access_service import AccessService
from application.services.import_app_service import ImportAppService
from apps.api.dependencies import get_access_service, get_current_user, get_import_service
from infra.db.models import UserModel

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/statements", response_model=ImportStatementResult)
async def import_statement(
    household_id: str = Form(...),
    account_id: str = Form(...),
    file: UploadFile = File(...),
    service: ImportAppService = Depends(get_import_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> ImportStatementResult:
    access_service.require_owner(household_id=household_id, user=current_user)
    return service.enqueue_statement_import(
        household_id=household_id,
        account_id=account_id,
        requested_by_user_id=current_user.id,
        filename=file.filename or "statement.csv",
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=await file.read(),
    )


@router.get("/jobs/{job_id}", response_model=ImportJobRead)
def get_import_job(
    job_id: str,
    household_id: str = Query(...),
    service: ImportAppService = Depends(get_import_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> ImportJobRead:
    access_service.require_owner(household_id=household_id, user=current_user)
    return ImportJobRead.model_validate(service.import_job_repo.get_for_household(job_id=job_id, household_id=household_id))
