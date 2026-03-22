from fastapi import APIRouter, Depends, Query

from application.dto.category import CategoryCreateRequest, CategoryRead
from application.services.category_app_service import CategoryAppService
from apps.api.dependencies import get_category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead)
def create_category(
    request: CategoryCreateRequest,
    service: CategoryAppService = Depends(get_category_service),
) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(request))


@router.get("", response_model=list[CategoryRead])
def list_categories(
    household_id: str = Query(...),
    service: CategoryAppService = Depends(get_category_service),
) -> list[CategoryRead]:
    return [CategoryRead.model_validate(category) for category in service.list_categories(household_id)]

