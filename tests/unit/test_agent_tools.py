from datetime import datetime, timezone
from decimal import Decimal

from application.dto.account import AccountCreateRequest
from application.dto.household import HouseholdBootstrapRequest
from application.dto.identity import IdentityBindingCreateRequest
from application.dto.transaction import TransactionCreateRequest
from application.services.account_app_service import AccountAppService
from application.services.agent_tool_service import AgentToolService
from application.services.analytics_app_service import AnalyticsAppService
from application.services.household_app_service import HouseholdAppService
from application.services.identity_binding_service import IdentityBindingService
from application.services.transaction_app_service import TransactionAppService
from application.services.errors import ValidationError
from domain.enums.account import AccountType
from domain.enums.identity import BindingRole
from domain.enums.transaction import TransactionDirection
from infra.config.settings import get_settings
from infra.db.repositories import (
    AccountRepository,
    AuditLogRepository,
    BindingRepository,
    BudgetRepository,
    CategoryRepository,
    HouseholdRepository,
    MemberRepository,
    TransactionRepository,
    UserRepository,
)


def _build_services(session):
    household_service = HouseholdAppService(UserRepository(session), HouseholdRepository(session), MemberRepository(session))
    account_service = AccountAppService(AccountRepository(session), HouseholdRepository(session), MemberRepository(session))
    identity_service = IdentityBindingService(
        BindingRepository(session),
        HouseholdRepository(session),
        MemberRepository(session),
        UserRepository(session),
        get_settings(),
    )
    transaction_service = TransactionAppService(
        TransactionRepository(session),
        AccountRepository(session),
        CategoryRepository(session),
        MemberRepository(session),
        HouseholdRepository(session),
    )
    analytics_service = AnalyticsAppService(
        TransactionRepository(session),
        AccountRepository(session),
        BudgetRepository(session),
        HouseholdRepository(session),
    )
    agent_service = AgentToolService(
        identity_service=identity_service,
        analytics_service=analytics_service,
        transaction_service=transaction_service,
        audit_repo=AuditLogRepository(session),
    )
    return household_service, account_service, identity_service, transaction_service, agent_service


def test_agent_tool_service_enforces_member_scope_and_idempotency(db_session) -> None:
    household_service, account_service, identity_service, _, agent_service = _build_services(db_session)
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(
            household_name="Test Home",
            owner_email="owner@example.com",
            owner_display_name="Owner",
        )
    )
    account = account_service.create_account(
        AccountCreateRequest(
            household_id=bootstrap.household_id,
            member_id=bootstrap.member_id,
            name="WeChat Wallet",
            type=AccountType.EWALLET,
            balance=Decimal("0"),
        )
    )
    identity_service.create_binding(
        IdentityBindingCreateRequest(
            provider="wechat",
            external_actor_id="owner-actor",
            user_id=bootstrap.user_id,
            member_id=bootstrap.member_id,
            household_id=bootstrap.household_id,
            role=BindingRole.OWNER,
        )
    )
    identity_service.create_binding(
        IdentityBindingCreateRequest(
            provider="wechat",
            external_actor_id="member-actor",
            user_id=bootstrap.user_id,
            member_id=bootstrap.member_id,
            household_id=bootstrap.household_id,
            role=BindingRole.MEMBER,
        )
    )

    payload = {
        "household_id": bootstrap.household_id,
        "account_id": account.id,
        "member_id": bootstrap.member_id,
        "direction": TransactionDirection.EXPENSE,
        "amount": "23.50",
        "txn_time": datetime(2026, 3, 20, 8, 30, tzinfo=timezone.utc).isoformat(),
        "description": "Breakfast",
        "idempotency_key": "manual-001",
    }
    first = agent_service.add_manual_transaction(
        provider="wechat",
        external_actor_id="owner-actor",
        household_id=bootstrap.household_id,
        payload=payload,
    )
    second = agent_service.add_manual_transaction(
        provider="wechat",
        external_actor_id="owner-actor",
        household_id=bootstrap.household_id,
        payload=payload,
    )
    denied = agent_service.query_member_spending(
        provider="wechat",
        external_actor_id="member-actor",
        household_id=bootstrap.household_id,
        month="2026-03",
    )

    assert first.ok is True
    assert second.ok is True
    assert second.data["idempotent_replay"] is True
    assert denied.ok is False
    assert denied.error_code == "owner_scope_required"


def test_binding_validation_rejects_duplicate_or_wrong_owner(db_session) -> None:
    household_service = HouseholdAppService(UserRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    identity_service = IdentityBindingService(
        BindingRepository(db_session),
        HouseholdRepository(db_session),
        MemberRepository(db_session),
        UserRepository(db_session),
        get_settings(),
    )
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(
            household_name="Validation Home",
            owner_email="owner-validation@example.com",
            owner_display_name="Owner Validation",
        )
    )
    other_user = UserRepository(db_session).get_or_create(email="other@example.com", display_name="Other")

    identity_service.create_binding(
        IdentityBindingCreateRequest(
            provider="wechat",
            external_actor_id="owner-actor",
            user_id=bootstrap.user_id,
            member_id=bootstrap.member_id,
            household_id=bootstrap.household_id,
            role=BindingRole.OWNER,
        )
    )

    try:
        identity_service.create_binding(
            IdentityBindingCreateRequest(
                provider="wechat",
                external_actor_id="owner-actor",
                user_id=bootstrap.user_id,
                member_id=bootstrap.member_id,
                household_id=bootstrap.household_id,
                role=BindingRole.OWNER,
            )
        )
        assert False, "expected duplicate binding validation"
    except ValidationError as exc:
        assert exc.code == "binding_already_exists"

    try:
        identity_service.create_binding(
            IdentityBindingCreateRequest(
                provider="wechat",
                external_actor_id="wrong-owner",
                user_id=other_user.id,
                member_id=bootstrap.member_id,
                household_id=bootstrap.household_id,
                role=BindingRole.OWNER,
            )
        )
        assert False, "expected wrong owner validation"
    except ValidationError as exc:
        assert exc.code == "binding_owner_user_mismatch"


def test_transaction_validation_rejects_cross_household_account(db_session) -> None:
    household_service = HouseholdAppService(UserRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    account_service = AccountAppService(AccountRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    transaction_service = TransactionAppService(
        TransactionRepository(db_session),
        AccountRepository(db_session),
        CategoryRepository(db_session),
        MemberRepository(db_session),
        HouseholdRepository(db_session),
    )

    first = household_service.bootstrap_household(
        HouseholdBootstrapRequest(
            household_name="Home 1",
            owner_email="owner-home-1@example.com",
            owner_display_name="Owner 1",
        )
    )
    second = household_service.bootstrap_household(
        HouseholdBootstrapRequest(
            household_name="Home 2",
            owner_email="owner-home-2@example.com",
            owner_display_name="Owner 2",
        )
    )
    account = account_service.create_account(
        AccountCreateRequest(
            household_id=first.household_id,
            member_id=first.member_id,
            name="Household 1 Wallet",
            type=AccountType.EWALLET,
            balance=Decimal("0"),
        )
    )

    try:
        transaction_service.create_manual_transaction(
            TransactionCreateRequest(
                household_id=second.household_id,
                account_id=account.id,
                member_id=second.member_id,
                direction=TransactionDirection.EXPENSE,
                amount="10.00",
                txn_time=datetime(2026, 3, 20, 8, 30, tzinfo=timezone.utc),
                description="Should fail",
            )
        )
        assert False, "expected account household validation"
    except ValidationError as exc:
        assert exc.code == "account_household_mismatch"
