import csv
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO

from adapters.importers.base import StatementImporter
from domain.enums.transaction import TransactionDirection
from domain.value_objects.normalized_transaction import NormalizedTransaction


class SimpleBankCSVImporter(StatementImporter):
    source_type = "bank_csv"

    def can_handle(self, filename: str, mime_type: str, sample: bytes) -> bool:
        text = sample.decode("utf-8-sig", errors="ignore")
        headers = text.splitlines()[0] if text else ""
        return "bank" in filename.lower() or "txn_time,amount,direction" in headers.lower()

    def parse(self, file_bytes: bytes) -> list[dict]:
        text = file_bytes.decode("utf-8-sig")
        return list(csv.DictReader(StringIO(text)))

    def normalize(self, raw_record: dict) -> NormalizedTransaction:
        direction = TransactionDirection(raw_record["direction"])
        return NormalizedTransaction(
            source_type=self.source_type,
            source_txn_id=raw_record.get("source_txn_id"),
            account_hint=raw_record.get("account_hint"),
            txn_time=datetime.fromisoformat(raw_record["txn_time"]).replace(tzinfo=timezone.utc),
            amount=Decimal(raw_record["amount"]).copy_abs(),
            currency=raw_record.get("currency", "CNY"),
            direction=direction,
            counterparty=raw_record.get("counterparty"),
            description=raw_record.get("description"),
            merchant_name=raw_record.get("merchant_name"),
            raw_payload=dict(raw_record),
        )

