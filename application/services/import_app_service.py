from application.dto.import_job import ImportStatementResult
from application.services.transaction_app_service import apply_transaction_to_balance
from adapters.importers.registry import ImporterRegistry
from domain.enums.transaction import ImportJobStatus
from domain.value_objects.dedupe_key import build_dedupe_key
from infra.db.repositories import AccountRepository, HouseholdRepository, ImportJobRepository, TransactionRepository


class ImportAppService:
    def __init__(
        self,
        importer_registry: ImporterRegistry,
        import_job_repo: ImportJobRepository,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        household_repo: HouseholdRepository,
    ) -> None:
        self.importer_registry = importer_registry
        self.import_job_repo = import_job_repo
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo
        self.household_repo = household_repo

    def import_statement(
        self,
        *,
        household_id: str,
        account_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> ImportStatementResult:
        self.household_repo.get(household_id)
        account = self.account_repo.get_for_household(account_id=account_id, household_id=household_id)
        job = self.import_job_repo.create(
            household_id=household_id,
            account_id=account_id,
            source_type="unknown",
            filename=filename,
            status=ImportJobStatus.PENDING,
        )
        imported_count = 0
        self.import_job_repo.set_status(job, status=ImportJobStatus.PROCESSING)
        try:
            importer = self.importer_registry.pick(filename=filename, mime_type=mime_type, sample=file_bytes[:2048])
            job.source_type = importer.source_type
            raw_records = importer.parse(file_bytes)
            for raw_record in raw_records:
                normalized = importer.normalize(raw_record)
                dedupe_key = build_dedupe_key(
                    household_id=household_id,
                    account_id=account_id,
                    txn_time=normalized.txn_time.isoformat(),
                    amount=str(normalized.amount),
                    counterparty=normalized.counterparty,
                    description=normalized.description,
                    source_txn_id=normalized.source_txn_id,
                )
                if self.transaction_repo.dedupe_exists(dedupe_key):
                    continue
                self.transaction_repo.create(
                    household_id=household_id,
                    account_id=account_id,
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
            self.import_job_repo.set_status(job, status=ImportJobStatus.COMPLETED, record_count=imported_count)
        except Exception as exc:
            self.import_job_repo.set_status(job, status=ImportJobStatus.FAILED, error_message=str(exc))
        return ImportStatementResult(
            job_id=job.id,
            status=job.status,
            imported_count=imported_count,
            error_message=job.error_message,
        )

    def get_import_job(self, job_id: str):
        return self.import_job_repo.get(job_id)
