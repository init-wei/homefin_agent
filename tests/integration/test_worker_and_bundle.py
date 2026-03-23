import json

from apps.mcp.server import run_tool
from apps.worker.tasks.openclaw_events import publish_import_completed
from application.dto.account import AccountCreateRequest
from application.dto.auth import AuthRegisterRequest
from application.dto.household import HouseholdBootstrapRequest
from application.dto.identity import IdentityBindingCreateRequest
from application.services.account_app_service import AccountAppService
from application.services.auth_service import AuthService
from application.services.household_app_service import HouseholdAppService
from application.services.identity_binding_service import IdentityBindingService
from domain.enums.account import AccountType
from domain.enums.identity import BindingRole
from infra.config.settings import get_settings
from infra.db.repositories import (
    AccountRepository,
    BindingRepository,
    HouseholdRepository,
    MemberRepository,
    UserRepository,
)


def test_worker_event_uses_openclaw_cli(monkeypatch) -> None:
    observed = {}

    def fake_run(command, check, capture_output, text):
        observed["command"] = command
        return None

    monkeypatch.setattr("subprocess.run", fake_run)
    publish_import_completed(household_id="h1", import_job_id="j1", imported_count=3)

    assert observed["command"][:3] == [get_settings().openclaw_cli_command, "system", "event"]


def test_worker_event_gracefully_handles_missing_openclaw(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("openclaw")

    monkeypatch.setattr("subprocess.run", fake_run)

    assert publish_import_completed(household_id="h1", import_job_id="j1", imported_count=3) == []


def test_bundle_mcp_config_exists() -> None:
    with open("integrations/openclaw/.mcp.json", "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert "homefin-agent" in payload["mcpServers"]


def test_mcp_run_tool_respects_owner_binding(db_session) -> None:
    auth_service = AuthService(UserRepository(db_session), get_settings())
    household_service = HouseholdAppService(UserRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    account_service = AccountAppService(AccountRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session))
    identity_service = IdentityBindingService(BindingRepository(db_session), HouseholdRepository(db_session), MemberRepository(db_session), UserRepository(db_session), get_settings())
    owner = auth_service.register_user(
        AuthRegisterRequest(
            email="owner3@example.com",
            display_name="Owner3",
            password="password123",
        )
    )
    bootstrap = household_service.bootstrap_household(
        HouseholdBootstrapRequest(
            household_name="Family C",
        ),
        owner,
    )
    account_service.create_account(
        AccountCreateRequest(
            household_id=bootstrap.household_id,
            member_id=bootstrap.member_id,
            name="Savings",
            type=AccountType.BANK,
            balance="1000.00",
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
    db_session.commit()

    result = run_tool(
        "query_net_worth_summary",
        provider="wechat",
        external_actor_id="owner-actor",
        household_id=bootstrap.household_id,
    )

    assert result["ok"] is True
    assert result["data"]["assets"] == "1000.00"
