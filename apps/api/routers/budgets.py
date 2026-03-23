from fastapi import APIRouter, Depends, Query

from application.dto.analytics import BudgetStatusRead
from application.dto.budget import BudgetCreateRequest, BudgetRead
from application.services.access_service import AccessService
from application.services.budget_app_service import BudgetAppService
from apps.api.dependencies import get_access_service, get_budget_service, get_current_user
from infra.db.models import UserModel

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead)
def create_budget(
    request: BudgetCreateRequest,
    service: BudgetAppService = Depends(get_budget_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> BudgetRead:
    access_service.require_owner(household_id=request.household_id, user=current_user)
    return BudgetRead.model_validate(service.create_budget(request))


@router.get("/status", response_model=BudgetStatusRead)
def get_budget_status(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: BudgetAppService = Depends(get_budget_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> BudgetStatusRead:
    scoped_member_id = access_service.resolve_member_scope(
        household_id=household_id,
        user=current_user,
        requested_member_id=member_id,
    )
    return service.get_budget_status(household_id=household_id, month=month, member_id=scoped_member_id)
