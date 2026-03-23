from pathlib import Path

from application.dto.import_job import ImportStatementResult
from application.services.errors import ValidationError
from application.services.transaction_app_service import apply_transaction_to_balance
from adapters.importers.registry import ImporterRegistry
from domain.enums.transaction import ImportJobStatus
from domain.value_objects.dedupe_key import build_dedupe_key
from infra.config.settings import Settings
from infra.db.models import ImportJobModel
from infra.db.repositories import AccountRepository, HouseholdRepository, ImportJobRepository, TransactionRepository


class ImportAppService:
    def __init__(
        self,
        importer_registry: ImporterRegistry,
        import_job_repo: ImportJobRepository,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        household_repo: HouseholdRepository,
        settings: Settings,
    ) -> None:
        self.importer_registry = importer_registry
        self.import_job_repo = import_job_repo
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo
        self.household_repo = household_repo
        self.storage_root = Path(settings.import_storage_dir)

    def enqueue_statement_import(
        self,
        *,
        household_id: str,
        account_id: str,
        requested_by_user_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> ImportStatementResult:
        self.household_repo.get(household_id)
        self.account_repo.get_for_household(account_id=account_id, household_id=household_id)
        job = self.import_job_repo.create(
            household_id=household_id,
            account_id=account_id,
            requested_by_user_id=requested_by_user_id,
            source_type="unknown",
            filename=filename,
            mime_type=mime_type,
            storage_path="",
            status=ImportJobStatus.PENDING,
        )
        try:
            storage_path = self._build_storage_path(job.id, filename)
            self._write_file(storage_path, file_bytes)
            job.storage_path = str(storage_path)
        except Exception as exc:
            self.import_job_repo.set_status(job, status=ImportJobStatus.FAILED, error_message=str(exc))
        return ImportStatementResult(
            job_id=job.id,
            status=job.status,
            imported_count=0,
            error_message=job.error_message,
        )

    def process_import_job(self, *, job_id: str) -> ImportJobModel:
        job = self.import_job_repo.get(job_id)
        if job.status == ImportJobStatus.COMPLETED:
            return job

        self.household_repo.get(job.household_id)
        if job.account_id is None:
            raise ValidationError("import_job_account_required", f"Import job {job.id} is missing an account_id.")
        account = self.account_repo.get_for_household(account_id=job.account_id, household_id=job.household_id)
        imported_count = 0
        self.import_job_repo.set_status(job, status=ImportJobStatus.PROCESSING, error_message=None)
        try:
            file_bytes = self._read_file(Path(job.storage_path))
            importer = self.importer_registry.pick(filename=job.filename, mime_type=job.mime_type, sample=file_bytes[:2048])
            job.source_type = importer.source_type
            raw_records = importer.parse(file_bytes)
            for raw_record in raw_records:
                normalized = importer.normalize(raw_record)
                dedupe_key = build_dedupe_key(
                    household_id=job.household_id,
                    account_id=job.account_id,
                    txn_time=normalized.txn_time.isoformat(),
                    amount=str(normalized.amount),
                    counterparty=normalized.counterparty,
                    description=normalized.description,
                    source_txn_id=normalized.source_txn_id,
                )
                if self.transaction_repo.dedupe_exists(dedupe_key):
                    continue
                self.transaction_repo.create(
                    household_id=job.household_id,
                    account_id=job.account_id,
                    member_id=None,
                    category_id=None,
                    import_job_id=job.id,
                    direction=normalized.direction,
                    amount=normalized.amount,
                    currency=normalized.currency,
                    txn_time=normalized.txn_time,
                    counterparty=normalized.counterparty,
                    description=normalized.description,
                    merchant_name=normalized.merchant_name,
                    is_shared=False,
                    dedupe_key=dedupe_key,
                    source_type=normalized.source_type,
                    source_txn_id=normalized.source_txn_id,
                    raw_payload=normalized.raw_payload,
                )
                account.balance = apply_transaction_to_balance(
                    current_balance=account.balance,
                    direction=normalized.direction,
                    amount=normalized.amount,
                )
                imported_count += 1
            self.import_job_repo.set_status(job, status=ImportJobStatus.COMPLETED, record_count=imported_count, error_message=None)
        except Exception as exc:
            self.import_job_repo.set_status(
                job,
                status=ImportJobStatus.FAILED,
                record_count=imported_count,
                error_message=str(exc),
            )
        return job

    def process_pending_jobs(self, *, limit: int = 20) -> list[ImportJobModel]:
        return [self.process_import_job(job_id=job.id) for job in self.import_job_repo.list_pending(limit=limit)]

    def get_import_job(self, job_id: str) -> ImportJobModel:
        return self.import_job_repo.get(job_id)

    def _build_storage_path(self, job_id: str, filename: str) -> Path:
        safe_name = Path(filename).name or "statement.csv"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        return self.storage_root / f"{job_id}-{safe_name}"

    def _write_file(self, path: Path, file_bytes: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file_bytes)

    def _read_file(self, path: Path) -> bytes:
        return path.read_bytes()
