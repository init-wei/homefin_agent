from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None

from sqlalchemy.orm import Session

from application.services.agent_tool_service import AgentToolService
from application.services.analytics_app_service import AnalyticsAppService
from application.services.identity_binding_service import IdentityBindingService
from application.services.transaction_app_service import TransactionAppService
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
from infra.db.session import init_db, session_scope


def build_agent_tool_service() -> tuple[AgentToolService, Session]:
    session = session_scope()
    settings = get_settings()
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
    ), session


def run_tool(method_name: str, **kwargs: Any) -> dict[str, Any]:
    service, session = build_agent_tool_service()
    try:
        result = getattr(service, method_name)(**kwargs)
        session.commit()
        return result.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if FastMCP:
    mcp = FastMCP("homefin-agent")

    @mcp.tool()
    def query_monthly_summary(provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "query_monthly_summary",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            month=month,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def query_category_breakdown(provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "query_category_breakdown",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            month=month,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def query_member_spending(provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "query_member_spending",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            month=month,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def query_budget_status(provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "query_budget_status",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            month=month,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def search_transactions(
        provider: str,
        external_actor_id: str,
        household_id: str,
        month: str | None = None,
        member_id: str | None = None,
        category_id: str | None = None,
        account_id: str | None = None,
        limit: int = 50,
        channel: str | None = None,
        route: str | None = None,
    ) -> dict[str, Any]:
        return run_tool(
            "search_transactions",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            month=month,
            member_id=member_id,
            category_id=category_id,
            account_id=account_id,
            limit=limit,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def query_net_worth_summary(provider: str, external_actor_id: str, household_id: str, channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "query_net_worth_summary",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def add_manual_transaction(provider: str, external_actor_id: str, household_id: str, payload: dict[str, Any], channel: str | None = None, route: str | None = None) -> dict[str, Any]:
        return run_tool(
            "add_manual_transaction",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            payload=payload,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def update_transaction_category(
        provider: str,
        external_actor_id: str,
        household_id: str,
        transaction_id: str,
        payload: dict[str, Any],
        channel: str | None = None,
        route: str | None = None,
    ) -> dict[str, Any]:
        return run_tool(
            "update_transaction_category",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            transaction_id=transaction_id,
            payload=payload,
            channel=channel,
            route=route,
        )

    @mcp.tool()
    def mark_shared_expense(
        provider: str,
        external_actor_id: str,
        household_id: str,
        transaction_id: str,
        payload: dict[str, Any],
        channel: str | None = None,
        route: str | None = None,
    ) -> dict[str, Any]:
        return run_tool(
            "mark_shared_expense",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            transaction_id=transaction_id,
            payload=payload,
            channel=channel,
            route=route,
        )


def main() -> None:
    if not FastMCP:  # pragma: no cover
        raise RuntimeError("Install the 'mcp' dependency to run the HomeFin MCP server.")
    init_db()
    mcp.run()


if __name__ == "__main__":
    main()
