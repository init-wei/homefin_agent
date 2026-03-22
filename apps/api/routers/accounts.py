from fastapi import APIRouter, Depends, Query

from application.dto.account import AccountCreateRequest, AccountRead
from application.services.account_app_service import AccountAppService
from apps.api.dependencies import get_account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead)
def create_account(
    request: AccountCreateRequest,
    service: AccountAppService = Depends(get_account_service),
) -> AccountRead:
    return AccountRead.model_validate(service.create_account(request))


@router.get("", response_model=list[AccountRead])
def list_accounts(
    household_id: str = Query(...),
    member_id: str | None = Query(None),
    service: AccountAppService = Depends(get_account_service),
) -> list[AccountRead]:
    return [AccountRead.model_validate(account) for account in service.list_accounts(household_id, member_id)]

