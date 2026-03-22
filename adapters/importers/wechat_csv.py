import csv
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO

from adapters.importers.base import StatementImporter
from domain.enums.transaction import TransactionDirection
from domain.value_objects.normalized_transaction import NormalizedTransaction


def _first(row: dict, *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


class WechatCSVImporter(StatementImporter):
    source_type = "wechat_csv"

    def can_handle(self, filename: str, mime_type: str, sample: bytes) -> bool:
        text = sample.decode("utf-8-sig", errors="ignore")
        return "wechat" in filename.lower() or ("交易时间" in text and "收/支" in text)

    def parse(self, file_bytes: bytes) -> list[dict]:
        text = file_bytes.decode("utf-8-sig")
        return list(csv.DictReader(StringIO(text)))

    def normalize(self, raw_record: dict) -> NormalizedTransaction:
        txn_time_raw = _first(raw_record, "交易时间", "txn_time")
        amount_raw = (_first(raw_record, "金额(元)", "金额", "amount") or "0").replace("¥", "").replace("￥", "").replace(",", "")
        direction_raw = _first(raw_record, "收/支", "direction") or "支出"
        description = _first(raw_record, "商品", "备注", "description")
        counterparty = _first(raw_record, "交易对方", "counterparty")
        source_txn_id = _first(raw_record, "交易单号", "流水号", "source_txn_id")
        txn_time = datetime.fromisoformat(txn_time_raw.replace("/", "-")).replace(tzinfo=timezone.utc)
        direction = TransactionDirection.EXPENSE if direction_raw in {"支出", "expense"} else TransactionDirection.INCOME
        return NormalizedTransaction(
            source_type=self.source_type,
            source_txn_id=source_txn_id,
            account_hint=_first(raw_record, "支付方式", "account_hint"),
            txn_time=txn_time,
            amount=Decimal(amount_raw).copy_abs(),
            currency="CNY",
            direction=direction,
            counterparty=counterparty,
            description=description,
            merchant_name=counterparty or description,
            raw_payload=dict(raw_record),
        )

