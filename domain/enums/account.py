from enum import StrEnum


class AccountType(StrEnum):
    CASH = "cash"
    BANK = "bank"
    CREDIT_CARD = "credit_card"
    EWALLET = "ewallet"
    ASSET = "asset"
    LIABILITY = "liability"

