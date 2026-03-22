from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from domain.enums.transaction import TransactionDirection


@dataclass(slots=True)
class NormalizedTransaction:
    source_type: str
    source_txn_id: str | None
    account_hint: str | None
    txn_time: datetime
    amount: Decimal
    currency: str
    direction: TransactionDirection
    counterparty: str | None
    description: str | None
    merchant_name: str | None
    raw_payload: dict[str, Any]

