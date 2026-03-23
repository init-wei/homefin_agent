from __future__ import annotations

import argparse
import time

from adapters.importers.registry import default_importer_registry
from application.services.import_app_service import ImportAppService
from apps.worker.tasks.openclaw_events import publish_budget_threshold_exceeded, publish_import_completed, publish_import_failed, publish_repayment_due_soon
from domain.enums.transaction import ImportJobStatus
from infra.config.settings import get_settings
from infra.db.repositories import AccountRepository, HouseholdRepository, ImportJobRepository, TransactionRepository
from infra.db.session import init_db, session_scope


def process_pending_import_jobs(*, limit: int = 20) -> list[str]:
    session = session_scope()
    try:
        service = ImportAppService(
            importer_registry=default_importer_registry(),
            import_job_repo=ImportJobRepository(session),
            transaction_repo=TransactionRepository(session),
            account_repo=AccountRepository(session),
            household_repo=HouseholdRepository(session),
            settings=get_settings(),
        )
        processed_jobs = service.process_pending_jobs(limit=limit)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    processed_ids: list[str] = []
    for job in processed_jobs:
        processed_ids.append(job.id)
        if job.status == ImportJobStatus.COMPLETED:
            publish_import_completed(
                household_id=job.household_id,
                import_job_id=job.id,
                imported_count=job.record_count,
            )
        elif job.status == ImportJobStatus.FAILED and job.error_message:
            publish_import_failed(
                household_id=job.household_id,
                import_job_id=job.id,
                error_message=job.error_message,
            )
    return processed_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="HomeFin background worker")
    parser.add_argument("--once", action="store_true", help="Process pending import jobs once and exit.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of jobs to process per poll.")
    args = parser.parse_args()

    init_db()
    if args.once:
        process_pending_import_jobs(limit=args.limit)
        return

    poll_interval = max(get_settings().worker_poll_interval_seconds, 1)
    while True:
        process_pending_import_jobs(limit=args.limit)
        time.sleep(poll_interval)

__all__ = [
    "process_pending_import_jobs",
    "publish_budget_threshold_exceeded",
    "publish_import_completed",
    "publish_import_failed",
    "publish_repayment_due_soon",
]


if __name__ == "__main__":
    main()
