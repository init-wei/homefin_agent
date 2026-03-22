from application.dto.analytics import BudgetStatusRead, NetWorthSummaryRead
from infra.db.repositories import AccountRepository, BudgetRepository, HouseholdRepository, TransactionRepository


class AnalyticsAppService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        budget_repo: BudgetRepository,
        household_repo: HouseholdRepository,
    ) -> None:
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo
        self.budget_repo = budget_repo
        self.household_repo = household_repo

    def get_monthly_summary(self, *, household_id: str, month: str, member_id: str | None = None) -> dict:
        self.household_repo.get(household_id)
        return self.transaction_repo.monthly_summary(household_id=household_id, month=month, member_id=member_id)

    def get_category_breakdown(self, *, household_id: str, month: str, member_id: str | None = None) -> list[dict]:
        self.household_repo.get(household_id)
        return self.transaction_repo.category_breakdown(household_id=household_id, month=month, member_id=member_id)

    def get_member_spending(self, *, household_id: str, month: str, member_id: str | None = None) -> list[dict]:
        self.household_repo.get(household_id)
        return self.transaction_repo.member_spending(household_id=household_id, month=month, member_id=member_id)

    def get_budget_status(self, *, household_id: str, month: str, member_id: str | None = None) -> BudgetStatusRead:
        self.household_repo.get(household_id)
        budget_limit = self.budget_repo.total_limit(household_id=household_id, month=month, member_id=member_id)
        summary = self.transaction_repo.monthly_summary(household_id=household_id, month=month, member_id=member_id)
        spent = summary["expense"]
        remaining = budget_limit - spent
        ratio = float(spent / budget_limit) if budget_limit else 0.0
        return BudgetStatusRead(
            month=month,
            budget_limit=budget_limit,
            spent=spent,
            remaining=remaining,
            utilization_ratio=ratio,
        )

    def get_net_worth_summary(self, *, household_id: str, member_id: str | None = None) -> NetWorthSummaryRead:
        self.household_repo.get(household_id)
        accounts = self.account_repo.list_by_household(household_id, member_id)
        assets = sum(account.balance for account in accounts if account.type.value in {"cash", "bank", "ewallet", "asset"})
        liabilities = sum(abs(account.balance) for account in accounts if account.type.value in {"credit_card", "liability"})
        return NetWorthSummaryRead(assets=assets, liabilities=liabilities, net_worth=assets - liabilities)

