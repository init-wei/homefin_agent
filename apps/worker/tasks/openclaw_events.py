from adapters.openclaw.gateway_client import OpenClawGatewayClient
from infra.config.settings import get_settings


def _client() -> OpenClawGatewayClient:
    return OpenClawGatewayClient(get_settings())


def publish_import_completed(*, household_id: str, import_job_id: str, imported_count: int) -> list[str]:
    return _client().emit_system_event(
        event_name="import_completed",
        payload={
            "household_id": household_id,
            "import_job_id": import_job_id,
            "imported_count": imported_count,
        },
    )


def publish_import_failed(*, household_id: str, import_job_id: str, error_message: str) -> list[str]:
    return _client().emit_system_event(
        event_name="import_failed",
        payload={
            "household_id": household_id,
            "import_job_id": import_job_id,
            "error_message": error_message,
        },
    )


def publish_budget_threshold_exceeded(*, household_id: str, month: str, utilization_ratio: float) -> list[str]:
    return _client().emit_system_event(
        event_name="budget_threshold_exceeded",
        payload={
            "household_id": household_id,
            "month": month,
            "utilization_ratio": utilization_ratio,
        },
    )


def publish_repayment_due_soon(*, household_id: str, account_id: str, due_date: str) -> list[str]:
    return _client().emit_system_event(
        event_name="repayment_due_soon",
        payload={
            "household_id": household_id,
            "account_id": account_id,
            "due_date": due_date,
        },
    )

