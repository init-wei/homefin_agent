from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.transaction import TransactionDirection


class TransactionCreateRequest(BaseModel):
    household_id: str
    account_id: str
    member_id: str | None = None
    category_id: str | None = None
    direction: TransactionDirection
    amount: Decimal = Field(gt=0)
    currency: str = "CNY"
    txn_time: datetime
    counterparty: str | None = None
    description: str | None = None
    merchant_name: str | None = None
    source_type: str = "manual"
    source_txn_id: str | None = None
    idempotency_key: str | None = None


class TransactionCategoryUpdateRequest(BaseModel):
    category_id: str
    idempotency_key: str | None = None


class SharedExpenseUpdateRequest(BaseModel):
    is_shared: bool
    idempotency_key: str | None = None


class TransactionSearchParams(BaseModel):
    household_id: str
    month: str | None = None
    member_id: str | None = None
    category_id: str | None = None
    account_id: str | None = None
    limit: int = 50


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    account_id: str
    member_id: str | None
    category_id: str | None
    direction: TransactionDirection
    amount: Decimal
    currency: str
    txn_time: datetime
    counterparty: str | None
    description: str | None
    merchant_name: str | None
    is_shared: bool
    source_type: str
    source_txn_id: str | None

