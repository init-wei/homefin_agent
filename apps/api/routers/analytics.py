from fastapi import APIRouter, Depends, Query

from application.dto.analytics import (
    BudgetStatusRead,
    CategoryBreakdownItem,
    MemberSpendingItem,
    MonthlySummaryRead,
    NetWorthSummaryRead,
)
from application.services.access_service import AccessService
from application.services.analytics_app_service import AnalyticsAppService
from apps.api.dependencies import get_access_service, get_analytics_service, get_current_user
from infra.db.models import UserModel

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/monthly-summary", response_model=MonthlySummaryRead)
def get_monthly_summary(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: AnalyticsAppService = Depends(get_analytics_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> MonthlySummaryRead:
    scoped_member_id = access_service.resolve_member_scope(
        household_id=household_id,
        user=current_user,
        requested_member_id=member_id,
    )
    return MonthlySummaryRead.model_validate(service.get_monthly_summary(household_id=household_id, month=month, member_id=scoped_member_id))


@router.get("/category-breakdown", response_model=list[CategoryBreakdownItem])
def get_category_breakdown(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: AnalyticsAppService = Depends(get_analytics_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[CategoryBreakdownItem]:
    scoped_member_id = access_service.resolve_member_scope(
        household_id=household_id,
        user=current_user,
        requested_member_id=member_id,
    )
    return [CategoryBreakdownItem.model_validate(item) for item in service.get_category_breakdown(household_id=household_id, month=month, member_id=scoped_member_id)]


@router.get("/member-spending", response_model=list[MemberSpendingItem])
def get_member_spending(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: AnalyticsAppService = Depends(get_analytics_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[MemberSpendingItem]:
    access_service.require_owner(household_id=household_id, user=current_user)
    if member_id:
        access_service.resolve_member_scope(household_id=household_id, user=current_user, requested_member_id=member_id)
    return [MemberSpendingItem.model_validate(item) for item in service.get_member_spending(household_id=household_id, month=month, member_id=member_id)]


@router.get("/budget-status", response_model=BudgetStatusRead)
def get_budget_status(
    household_id: str = Query(...),
    month: str = Query(...),
    member_id: str | None = Query(None),
    service: AnalyticsAppService = Depends(get_analytics_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> BudgetStatusRead:
    scoped_member_id = access_service.resolve_member_scope(
        household_id=household_id,
        user=current_user,
        requested_member_id=member_id,
    )
    return service.get_budget_status(household_id=household_id, month=month, member_id=scoped_member_id)


@router.get("/net-worth", response_model=NetWorthSummaryRead)
def get_net_worth(
    household_id: str = Query(...),
    member_id: str | None = Query(None),
    service: AnalyticsAppService = Depends(get_analytics_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> NetWorthSummaryRead:
    access_service.require_owner(household_id=household_id, user=current_user)
    if member_id:
        access_service.resolve_member_scope(household_id=household_id, user=current_user, requested_member_id=member_id)
    return service.get_net_worth_summary(household_id=household_id, member_id=member_id)
