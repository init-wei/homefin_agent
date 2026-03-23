from datetime import datetime, timezone
from decimal import Decimal

import pytest

from application.dto.account import AccountCreateRequest
from application.dto.auth import AuthRegisterRequest
from application.dto.household import HouseholdBootstrapRequest
from application.dto.identity import IdentityBindingCreateRequest
from application.dto.transaction import TransactionCreateRequest
from application.services.account_app_service import AccountAppService
from application.services.access_service import AccessService
from application.services.agent_tool_service import AgentToolService
from application.services.analytics_app_service import AnalyticsAppService
from application.services.auth_service import AuthService
from application.services.household_app_service import HouseholdAppService
from application.services.identity_binding_service import IdentityBindingService
from application.services.transaction_app_service import TransactionAppService
from application.services.errors import PermissionDenied, ValidationError
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
    auth_service = AuthService(UserRepository(session), get_settings())
    household_service = HouseholdAppService(UserRepository(session), HouseholdRepository(session), MemberRepository(session))
    account_service = AccountAppService(AccountRepository(session), HouseholdRepository(session), MemberRepository(session))
    access_service = AccessService(HouseholdRepository(session), MemberRepository(session))
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
    return auth_service, household_service, account_service, access_service, identity_service, transaction_service, agent_service


def _register_user(auth_service: AuthService, *, email: str, display_name: str):
    return auth_service.register_user(
        AuthRegisterRequest(
            email=email,
            display_name=display_name,
            password="password123",
        )
    )


def test_agent_tool_service_enforces_member_scope_and_idempotency(db_session) -> None:
    auth_service, household_service, account_service, _, identity_service, _, agent_service = _build_services(db_session)
    owner = _register_user(auth_service, email="owner@example.com", display_name="Owner")
    member_user = _register_user(auth_service, email="member@example.com", display_name="Member")
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(household_name="Test Home"),
        owner,
    )
    member = MemberRepository(db_session).create(
        household_id=bootstrap.household_id,
        user_id=member_user.id,
        name="Member",
        role="member",
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
            user_id=member_user.id,
            member_id=member.id,
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
    auth_service = AuthService(UserRepository(db_session), get_settings())
    household_service = HouseholdAppService(UserRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    identity_service = IdentityBindingService(
        BindingRepository(db_session),
        HouseholdRepository(db_session),
        MemberRepository(db_session),
        UserRepository(db_session),
        get_settings(),
    )
    owner = _register_user(auth_service, email="owner-validation@example.com", display_name="Owner Validation")
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(household_name="Validation Home"),
        owner,
    )
    other_user = _register_user(auth_service, email="other@example.com", display_name="Other")

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

    with pytest.raises(ValidationError) as duplicate:
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
    assert duplicate.value.code == "binding_already_exists"

    with pytest.raises(ValidationError) as wrong_owner:
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
    assert wrong_owner.value.code == "binding_owner_user_mismatch"


def test_transaction_validation_rejects_cross_household_account(db_session) -> None:
    auth_service = AuthService(UserRepository(db_session), get_settings())
    household_service = HouseholdAppService(UserRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    account_service = AccountAppService(AccountRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    transaction_service = TransactionAppService(
        TransactionRepository(db_session),
        AccountRepository(db_session),
        CategoryRepository(db_session),
        MemberRepository(db_session),
        HouseholdRepository(db_session),
    )
    owner_one = _register_user(auth_service, email="owner-home-1@example.com", display_name="Owner 1")
    owner_two = _register_user(auth_service, email="owner-home-2@example.com", display_name="Owner 2")

    first = household_service.bootstrap_household(
        HouseholdBootstrapRequest(household_name="Home 1"),
        owner_one,
    )
    second = household_service.bootstrap_household(
        HouseholdBootstrapRequest(household_name="Home 2"),
        owner_two,
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

    with pytest.raises(ValidationError) as mismatch:
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
    assert mismatch.value.code == "account_household_mismatch"


def test_access_service_restricts_member_scope(db_session) -> None:
    auth_service, household_service, _, access_service, _, _, _ = _build_services(db_session)
    owner = _register_user(auth_service, email="scope-owner@example.com", display_name="Scope Owner")
    member_user = _register_user(auth_service, email="scope-member@example.com", display_name="Scope Member")
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(household_name="Scope Home"),
        owner,
    )
    member = MemberRepository(db_session).create(
        household_id=bootstrap.household_id,
        user_id=member_user.id,
        name="Scope Member",
        role="member",
    )

    assert access_service.resolve_member_scope(
        household_id=bootstrap.household_id,
        user=member_user,
        requested_member_id=None,
    ) == member.id

    with pytest.raises(PermissionDenied) as exc_info:
        access_service.resolve_member_scope(
            household_id=bootstrap.household_id,
            user=member_user,
            requested_member_id=bootstrap.member_id,
        )
    assert exc_info.value.code == "member_scope_mismatch"
