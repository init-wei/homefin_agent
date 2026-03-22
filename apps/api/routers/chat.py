from fastapi import APIRouter, Depends, Query

from application.dto.audit import AuditLogRead
from application.dto.chat import ChatDispatchRequest, ChatDispatchResponse
from application.dto.identity import IdentityBindingCreateRequest, IdentityBindingRead
from application.services.chat_app_service import ChatAppService
from application.services.identity_binding_service import IdentityBindingService
from apps.api.dependencies import get_audit_repo, get_chat_service, get_identity_binding_service
from infra.db.repositories import AuditLogRepository

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/bindings", response_model=IdentityBindingRead)
def create_identity_binding(
    request: IdentityBindingCreateRequest,
    service: IdentityBindingService = Depends(get_identity_binding_service),
) -> IdentityBindingRead:
    return IdentityBindingRead.model_validate(service.create_binding(request))


@router.post("/messages", response_model=ChatDispatchResponse)
def dispatch_message(
    request: ChatDispatchRequest,
    service: ChatAppService = Depends(get_chat_service),
) -> ChatDispatchResponse:
    return service.dispatch_to_openclaw(request)


@router.get("/audits", response_model=list[AuditLogRead])
def list_audits(
    household_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    repo: AuditLogRepository = Depends(get_audit_repo),
) -> list[AuditLogRead]:
    return [AuditLogRead.model_validate(log) for log in repo.list_recent(household_id=household_id, limit=limit)]

