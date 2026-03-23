from fastapi import APIRouter, Depends

from application.dto.household import HouseholdBootstrapRead, HouseholdBootstrapRequest
from application.services.household_app_service import HouseholdAppService
from apps.api.dependencies import get_current_user, get_household_service
from infra.db.models import UserModel

router = APIRouter(prefix="/households", tags=["households"])


@router.post("/bootstrap", response_model=HouseholdBootstrapRead)
def bootstrap_household(
    request: HouseholdBootstrapRequest,
    service: HouseholdAppService = Depends(get_household_service),
    current_user: UserModel = Depends(get_current_user),
) -> HouseholdBootstrapRead:
    return service.bootstrap_household(request, current_user)
