from pydantic import BaseModel, ConfigDict

from domain.enums.transaction import ImportJobStatus


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    account_id: str | None
    requested_by_user_id: str | None
    source_type: str
    filename: str
    mime_type: str
    storage_path: str
    status: ImportJobStatus
    record_count: int
    error_message: str | None


class ImportStatementResult(BaseModel):
    job_id: str
    status: ImportJobStatus
    imported_count: int
    error_message: str | None = None
