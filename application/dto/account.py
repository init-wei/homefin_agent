from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from domain.enums.account import AccountType


class AccountCreateRequest(BaseModel):
    household_id: str
    member_id: str | None = None
    name: str
    type: AccountType
    currency: str = "CNY"
    institution_name: str | None = None
    balance: Decimal = Decimal("0")


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    member_id: str | None
    name: str
    type: AccountType
    currency: str
    institution_name: str | None
    balance: Decimal

