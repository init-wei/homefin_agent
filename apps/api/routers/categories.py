from fastapi import APIRouter, Depends, Query

from application.dto.category import CategoryCreateRequest, CategoryRead
from application.services.category_app_service import CategoryAppService
from application.services.access_service import AccessService
from apps.api.dependencies import get_access_service, get_category_service, get_current_user
from infra.db.models import UserModel

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead)
def create_category(
    request: CategoryCreateRequest,
    service: CategoryAppService = Depends(get_category_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> CategoryRead:
    access_service.require_owner(household_id=request.household_id, user=current_user)
    return CategoryRead.model_validate(service.create_category(request))


@router.get("", response_model=list[CategoryRead])
def list_categories(
    household_id: str = Query(...),
    service: CategoryAppService = Depends(get_category_service),
    access_service: AccessService = Depends(get_access_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[CategoryRead]:
    access_service.resolve_household_access(household_id=household_id, user=current_user)
    return [CategoryRead.model_validate(category) for category in service.list_categories(household_id)]
