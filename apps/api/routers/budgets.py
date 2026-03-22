from fastapi import APIRouter, Depends, Query

from application.dto.analytics import BudgetStatusRead
from application.dto.budget import BudgetCreateRequest, BudgetRead
from application.services.budget_app_service import BudgetAppService
from apps.api.dependencies import get_budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead)
def create_budget(
    request: BudgetCreateRequest,
    service: BudgetAppService = Depends(get_budget_service),
) -> BudgetRead:
    return BudgetRead.model_validate(service.create_budget(request))


@router.get("/status", response_model=BudgetStatusRead)
def get_budget_status(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: BudgetAppService = Depends(get_budget_service),
) -> BudgetStatusRead:
    return service.get_budget_status(household_id=household_id, month=month, member_id=member_id)

