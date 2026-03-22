from decimal import Decimal

from pydantic import BaseModel


class MonthlySummaryRead(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    net: Decimal
    transaction_count: int


class CategoryBreakdownItem(BaseModel):
    category: str
    total: Decimal


class MemberSpendingItem(BaseModel):
    member_id: str
    member_name: str
    total: Decimal


class BudgetStatusRead(BaseModel):
    month: str
    budget_limit: Decimal
    spent: Decimal
    remaining: Decimal
    utilization_ratio: float


class NetWorthSummaryRead(BaseModel):
    assets: Decimal
    liabilities: Decimal
    net_worth: Decimal

