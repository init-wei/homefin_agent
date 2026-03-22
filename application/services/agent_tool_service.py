from __future__ import annotations

from typing import Any, Callable

from application.dto.transaction import (
    SharedExpenseUpdateRequest,
    TransactionCategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionSearchParams,
)
from application.services.analytics_app_service import AnalyticsAppService
from application.services.errors import PermissionDenied, ServiceError
from application.services.identity_binding_service import IdentityBindingService
from application.services.transaction_app_service import TransactionAppService
from domain.entities.contracts import AgentExecutionContext, AgentToolResult
from domain.enums.identity import BindingRole
from infra.db.repositories import AuditLogRepository


class AgentToolService:
    def __init__(
        self,
        identity_service: IdentityBindingService,
        analytics_service: AnalyticsAppService,
        transaction_service: TransactionAppService,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.identity_service = identity_service
        self.analytics_service = analytics_service
        self.transaction_service = transaction_service
        self.audit_repo = audit_repo

    def query_monthly_summary(self, *, provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> AgentToolResult:
        return self._execute_read(
            tool_name="query_monthly_summary",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"month": month},
            handler=lambda context: self.analytics_service.get_monthly_summary(
                household_id=household_id,
                month=month,
                member_id=self._member_scope(context, None),
            ),
        )

    def query_category_breakdown(self, *, provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> AgentToolResult:
        return self._execute_read(
            tool_name="query_category_breakdown",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"month": month},
            handler=lambda context: {
                "month": month,
                "items": self.analytics_service.get_category_breakdown(
                    household_id=household_id,
                    month=month,
                    member_id=self._member_scope(context, None),
                ),
            },
        )

    def query_member_spending(self, *, provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> AgentToolResult:
        return self._execute_read(
            tool_name="query_member_spending",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"month": month},
            handler=lambda context: {
                "month": month,
                "items": self.analytics_service.get_member_spending(
                    household_id=household_id,
                    month=month,
                    member_id=self._require_owner(context),
                ),
            },
        )

    def query_budget_status(self, *, provider: str, external_actor_id: str, household_id: str, month: str, channel: str | None = None, route: str | None = None) -> AgentToolResult:
        return self._execute_read(
            tool_name="query_budget_status",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"month": month},
            handler=lambda context: self.analytics_service.get_budget_status(
                household_id=household_id,
                month=month,
                member_id=self._require_owner(context),
            ).model_dump(),
        )

    def search_transactions(
        self,
        *,
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
    ) -> AgentToolResult:
        return self._execute_read(
            tool_name="search_transactions",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={
                "month": month,
                "member_id": member_id,
                "category_id": category_id,
                "account_id": account_id,
                "limit": limit,
            },
            handler=lambda context: {
                "items": [
                    {
                        "id": txn.id,
                        "amount": str(txn.amount),
                        "direction": txn.direction.value,
                        "txn_time": txn.txn_time.isoformat(),
                        "counterparty": txn.counterparty,
                        "description": txn.description,
                        "member_id": txn.member_id,
                    }
                    for txn in self.transaction_service.search_transactions(
                        TransactionSearchParams(
                            household_id=household_id,
                            month=month,
                            member_id=self._member_scope(context, member_id),
                            category_id=category_id,
                            account_id=account_id,
                            limit=limit,
                        )
                    )
                ]
            },
        )

    def query_net_worth_summary(self, *, provider: str, external_actor_id: str, household_id: str, channel: str | None = None, route: str | None = None) -> AgentToolResult:
        return self._execute_read(
            tool_name="query_net_worth_summary",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={},
            handler=lambda context: self.analytics_service.get_net_worth_summary(
                household_id=household_id,
                member_id=self._require_owner(context),
            ).model_dump(),
        )

    def add_manual_transaction(
        self,
        *,
        provider: str,
        external_actor_id: str,
        household_id: str,
        payload: dict[str, Any],
        channel: str | None = None,
        route: str | None = None,
    ) -> AgentToolResult:
        request = TransactionCreateRequest(**payload)
        return self._execute_write(
            tool_name="add_manual_transaction",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload=payload,
            idempotency_key=request.idempotency_key,
            handler=lambda _context: self.transaction_service.create_manual_transaction(request),
            serializer=lambda txn: {"transaction_id": txn.id, "amount": str(txn.amount)},
        )

    def update_transaction_category(
        self,
        *,
        provider: str,
        external_actor_id: str,
        household_id: str,
        transaction_id: str,
        payload: dict[str, Any],
        channel: str | None = None,
        route: str | None = None,
    ) -> AgentToolResult:
        request = TransactionCategoryUpdateRequest(**payload)
        return self._execute_write(
            tool_name="update_transaction_category",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"transaction_id": transaction_id, **payload},
            idempotency_key=request.idempotency_key,
            handler=lambda _context: self.transaction_service.update_transaction_category(transaction_id=transaction_id, request=request),
            serializer=lambda txn: {"transaction_id": txn.id, "category_id": txn.category_id},
        )

    def mark_shared_expense(
        self,
        *,
        provider: str,
        external_actor_id: str,
        household_id: str,
        transaction_id: str,
        payload: dict[str, Any],
        channel: str | None = None,
        route: str | None = None,
    ) -> AgentToolResult:
        request = SharedExpenseUpdateRequest(**payload)
        return self._execute_write(
            tool_name="mark_shared_expense",
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload={"transaction_id": transaction_id, **payload},
            idempotency_key=request.idempotency_key,
            handler=lambda _context: self.transaction_service.mark_shared_expense(transaction_id=transaction_id, request=request),
            serializer=lambda txn: {"transaction_id": txn.id, "is_shared": txn.is_shared},
        )

    def _execute_read(
        self,
        *,
        tool_name: str,
        provider: str,
        external_actor_id: str,
        household_id: str,
        channel: str | None,
        route: str | None,
        args_payload: dict[str, Any],
        handler: Callable[[AgentExecutionContext], dict[str, Any]],
    ) -> AgentToolResult:
        return self._execute(
            tool_name=tool_name,
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload=args_payload,
            idempotency_key=None,
            write=False,
            handler=handler,
        )

    def _execute_write(
        self,
        *,
        tool_name: str,
        provider: str,
        external_actor_id: str,
        household_id: str,
        channel: str | None,
        route: str | None,
        args_payload: dict[str, Any],
        idempotency_key: str | None,
        handler: Callable[[AgentExecutionContext], Any],
        serializer: Callable[[Any], dict[str, Any]],
    ) -> AgentToolResult:
        return self._execute(
            tool_name=tool_name,
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
            channel=channel,
            route=route,
            args_payload=args_payload,
            idempotency_key=idempotency_key,
            write=True,
            handler=lambda context: serializer(handler(context)),
        )

    def _execute(
        self,
        *,
        tool_name: str,
        provider: str,
        external_actor_id: str,
        household_id: str,
        channel: str | None,
        route: str | None,
        args_payload: dict[str, Any],
        idempotency_key: str | None,
        write: bool,
        handler: Callable[[AgentExecutionContext], dict[str, Any]],
    ) -> AgentToolResult:
        try:
            context = self.identity_service.resolve_context(
                provider=provider,
                external_actor_id=external_actor_id,
                household_id=household_id,
                channel=channel,
                route=route,
            )
        except ServiceError as error:
            audit = self.audit_repo.create(
                tool_name=tool_name,
                household_id=household_id,
                user_id=None,
                member_id=None,
                session_key=f"agent:homefin:{household_id}:{provider}:{external_actor_id}",
                role="anonymous",
                can_write=False,
                ok=False,
                error_code=error.code,
                args_payload=args_payload,
                result_payload={"error": error.message},
                idempotency_key=idempotency_key,
            )
            return AgentToolResult(ok=False, data=None, display_text=error.message, audit_id=audit.id, error_code=error.code)
        if write and not context.can_write:
            return self._error_result(
                tool_name=tool_name,
                context=context,
                args_payload=args_payload,
                idempotency_key=idempotency_key,
                error=PermissionDenied("write_forbidden", "This actor does not have write permissions."),
            )
        if write and idempotency_key:
            existing = self.audit_repo.find_success_by_idempotency(
                tool_name=tool_name,
                household_id=household_id,
                user_id=context.acting_user_id,
                idempotency_key=idempotency_key,
            )
            if existing:
                return AgentToolResult(
                    ok=True,
                    data=existing.result_payload | {"idempotent_replay": True},
                    display_text="Idempotent replay; previous successful result reused.",
                    audit_id=existing.id,
                    error_code=None,
                )
        try:
            data = handler(context)
            audit = self.audit_repo.create(
                tool_name=tool_name,
                household_id=household_id,
                user_id=context.acting_user_id,
                member_id=context.member_id,
                session_key=context.session_key,
                role=context.role.value,
                can_write=context.can_write,
                ok=True,
                error_code=None,
                args_payload=args_payload,
                result_payload=data,
                idempotency_key=idempotency_key,
            )
            return AgentToolResult(
                ok=True,
                data=data,
                display_text=f"{tool_name} completed successfully.",
                audit_id=audit.id,
                error_code=None,
            )
        except ServiceError as error:
            return self._error_result(
                tool_name=tool_name,
                context=context,
                args_payload=args_payload,
                idempotency_key=idempotency_key,
                error=error,
            )

    def _error_result(
        self,
        *,
        tool_name: str,
        context: AgentExecutionContext,
        args_payload: dict[str, Any],
        idempotency_key: str | None,
        error: ServiceError,
    ) -> AgentToolResult:
        audit = self.audit_repo.create(
            tool_name=tool_name,
            household_id=context.household_id,
            user_id=context.acting_user_id,
            member_id=context.member_id,
            session_key=context.session_key,
            role=context.role.value,
            can_write=context.can_write,
            ok=False,
            error_code=error.code,
            args_payload=args_payload,
            result_payload={"error": error.message},
            idempotency_key=idempotency_key,
        )
        return AgentToolResult(
            ok=False,
            data=None,
            display_text=error.message,
            audit_id=audit.id,
            error_code=error.code,
        )

    def _require_owner(self, context: AgentExecutionContext) -> str | None:
        if context.role != BindingRole.OWNER:
            raise PermissionDenied("owner_scope_required", "This tool is only available to household owners.")
        return None

    def _member_scope(self, context: AgentExecutionContext, requested_member_id: str | None) -> str | None:
        if context.role == BindingRole.OWNER:
            return requested_member_id
        if not context.member_id:
            raise PermissionDenied("member_scope_missing", "This member binding is missing a member_id.")
        if requested_member_id and requested_member_id != context.member_id:
            raise PermissionDenied("member_scope_mismatch", "Members can only query their own records.")
        return context.member_id
