from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from adapters.importers.registry import default_importer_registry
from adapters.openclaw.gateway_client import OpenClawGatewayClient
from application.services.account_app_service import AccountAppService
from application.services.access_service import AccessService
from application.services.agent_tool_service import AgentToolService
from application.services.analytics_app_service import AnalyticsAppService
from application.services.auth_service import AuthService, decode_access_token
from application.services.budget_app_service import BudgetAppService
from application.services.category_app_service import CategoryAppService
from application.services.chat_app_service import ChatAppService
from application.services.errors import AuthenticationError
from application.services.household_app_service import HouseholdAppService
from application.services.identity_binding_service import IdentityBindingService
from application.services.import_app_service import ImportAppService
from application.services.transaction_app_service import TransactionAppService
from infra.db.models import UserModel
from infra.config.settings import Settings, get_settings
from infra.db.repositories import (
    AccountRepository,
    AuditLogRepository,
    BindingRepository,
    BudgetRepository,
    CategoryRepository,
    HouseholdRepository,
    ImportJobRepository,
    MemberRepository,
    TransactionRepository,
    UserRepository,
)
from infra.db.session import session_scope

bearer_scheme = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    session = session_scope()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_settings_dependency() -> Settings:
    return get_settings()


def get_auth_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> AuthService:
    return AuthService(UserRepository(session), settings)


def get_access_service(session: Session = Depends(get_db_session)) -> AccessService:
    return AccessService(HouseholdRepository(session), MemberRepository(session))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> UserModel:
    if credentials is None:
        raise AuthenticationError("authentication_required", "Bearer token is required.")
    payload = decode_access_token(credentials.credentials, settings)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise AuthenticationError("invalid_token", "Access token subject is invalid.")
    return UserRepository(session).get(user_id)


def get_household_service(session: Session = Depends(get_db_session)) -> HouseholdAppService:
    return HouseholdAppService(
        user_repo=UserRepository(session),
        household_repo=HouseholdRepository(session),
        member_repo=MemberRepository(session),
    )


def get_account_service(session: Session = Depends(get_db_session)) -> AccountAppService:
    return AccountAppService(AccountRepository(session), HouseholdRepository(session), MemberRepository(session))


def get_category_service(session: Session = Depends(get_db_session)) -> CategoryAppService:
    return CategoryAppService(CategoryRepository(session), HouseholdRepository(session))


def get_budget_service(session: Session = Depends(get_db_session)) -> BudgetAppService:
    return BudgetAppService(
        BudgetRepository(session),
        TransactionRepository(session),
        HouseholdRepository(session),
        CategoryRepository(session),
        MemberRepository(session),
    )


def get_transaction_service(session: Session = Depends(get_db_session)) -> TransactionAppService:
    return TransactionAppService(
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        category_repo=CategoryRepository(session),
        member_repo=MemberRepository(session),
        household_repo=HouseholdRepository(session),
    )


def get_analytics_service(session: Session = Depends(get_db_session)) -> AnalyticsAppService:
    return AnalyticsAppService(
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        budget_repo=BudgetRepository(session),
        household_repo=HouseholdRepository(session),
    )


def get_import_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> ImportAppService:
    return ImportAppService(
        importer_registry=default_importer_registry(),
        import_job_repo=ImportJobRepository(session),
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        household_repo=HouseholdRepository(session),
        settings=settings,
    )


def get_identity_binding_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> IdentityBindingService:
    return IdentityBindingService(
        binding_repo=BindingRepository(session),
        household_repo=HouseholdRepository(session),
        member_repo=MemberRepository(session),
        user_repo=UserRepository(session),
        settings=settings,
    )


def get_chat_service(settings: Settings = Depends(get_settings_dependency)) -> ChatAppService:
    return ChatAppService(OpenClawGatewayClient(settings))


def get_agent_tool_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> AgentToolService:
    analytics_service = AnalyticsAppService(
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        budget_repo=BudgetRepository(session),
        household_repo=HouseholdRepository(session),
    )
    transaction_service = TransactionAppService(
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        category_repo=CategoryRepository(session),
        member_repo=MemberRepository(session),
        household_repo=HouseholdRepository(session),
    )
    identity_service = IdentityBindingService(
        binding_repo=BindingRepository(session),
        household_repo=HouseholdRepository(session),
        member_repo=MemberRepository(session),
        user_repo=UserRepository(session),
        settings=settings,
    )
    return AgentToolService(
        identity_service=identity_service,
        analytics_service=analytics_service,
        transaction_service=transaction_service,
        audit_repo=AuditLogRepository(session),
    )


def get_audit_repo(session: Session = Depends(get_db_session)) -> AuditLogRepository:
    return AuditLogRepository(session)
