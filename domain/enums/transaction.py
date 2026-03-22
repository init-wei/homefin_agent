from enum import StrEnum


class TransactionDirection(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class ImportJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
