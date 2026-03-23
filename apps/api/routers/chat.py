from fastapi import APIRouter, Depends, Query

from application.dto.audit import AuditLogRead
from application.dto.chat import ChatDispatchRequest, ChatDispatchResponse
from application.dto.identity import IdentityBindingCreateRequest, IdentityBindingRead
from application.services.access_service import AccessService
from application.services.chat_app_service import ChatAppService
from application.services.identity_binding_service import IdentityBindingService
from apps.api.dependencies import get_access_service, get_audit_repo, get_chat_service, get_current_user, get_identity_binding_service
from infra.db.models import UserModel
from infra.db.repositories import AuditLogRepository

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/bindings", response_model=IdentityBindingRead)
def create_identity_binding(
    request: IdentityBindingCreateRequest,
    service: IdentityBindingService = Depends(get_identity_binding_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> IdentityBindingRead:
    access_service.require_owner(household_id=request.household_id, user=current_user)
    return IdentityBindingRead.model_validate(service.create_binding(request))


@router.post("/messages", response_model=ChatDispatchResponse)
def dispatch_message(
    request: ChatDispatchRequest,
    service: ChatAppService = Depends(get_chat_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> ChatDispatchResponse:
    access_service.resolve_household_access(household_id=request.household_id, user=current_user)
    return service.dispatch_to_openclaw(request)


@router.get("/audits", response_model=list[AuditLogRead])
def list_audits(
    household_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    repo: AuditLogRepository = Depends(get_audit_repo),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[AuditLogRead]:
    access_service.require_owner(household_id=household_id, user=current_user)
    return [AuditLogRead.model_validate(log) for log in repo.list_recent(household_id=household_id, limit=limit)]
