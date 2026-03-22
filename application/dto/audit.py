from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tool_name: str
    household_id: str
    user_id: str | None
    member_id: str | None
    role: str
    can_write: bool
    ok: bool
    error_code: str | None
    args_preview: str
    result_preview: str
    idempotency_key: str | None
    created_at: datetime

