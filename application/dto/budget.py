from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreateRequest(BaseModel):
    household_id: str
    month: str
    category_id: str | None = None
    member_id: str | None = None
    limit_amount: Decimal = Field(gt=0)


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    month: str
    category_id: str | None
    member_id: str | None
    limit_amount: Decimal

