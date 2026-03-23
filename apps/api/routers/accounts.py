from fastapi import APIRouter, Depends, Query

from application.dto.account import AccountCreateRequest, AccountRead
from application.services.account_app_service import AccountAppService
from application.services.access_service import AccessService
from apps.api.dependencies import get_access_service, get_account_service, get_current_user
from infra.db.models import UserModel

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead)
def create_account(
    request: AccountCreateRequest,
    service: AccountAppService = Depends(get_account_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> AccountRead:
    access_service.require_owner(household_id=request.household_id, user=current_user)
    return AccountRead.model_validate(service.create_account(request))


@router.get("", response_model=list[AccountRead])
def list_accounts(
    household_id: str = Query(...),
    member_id: str | None = Query(None),
    service: AccountAppService = Depends(get_account_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[AccountRead]:
    scoped_member_id = access_service.resolve_member_scope(
        household_id=household_id,
        user=current_user,
        requested_member_id=member_id,
    )
    return [AccountRead.model_validate(account) for account in service.list_accounts(household_id, scoped_member_id)]
