from fastapi import APIRouter, Depends

from application.dto.auth import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse, UserRead
from application.services.auth_service import AuthService
from apps.api.dependencies import get_auth_service, get_current_user
from infra.db.models import UserModel

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
def register(
    request: AuthRegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    user = service.register_user(request)
    return service.issue_token_response(user)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    request: AuthLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    user = service.authenticate(request)
    return service.issue_token_response(user)


@router.get("/me", response_model=UserRead)
def me(current_user: UserModel = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
