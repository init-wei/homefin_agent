from decimal import Decimal

from application.dto.analytics import BudgetStatusRead
from application.dto.budget import BudgetCreateRequest
from infra.db.repositories import CategoryRepository, MemberRepository
from infra.db.models import BudgetModel
from infra.db.repositories import BudgetRepository, HouseholdRepository, TransactionRepository


class BudgetAppService:
    def __init__(
        self,
        budget_repo: BudgetRepository,
        transaction_repo: TransactionRepository,
        household_repo: HouseholdRepository,
        category_repo: CategoryRepository,
        member_repo: MemberRepository,
    ) -> None:
        self.budget_repo = budget_repo
        self.transaction_repo = transaction_repo
        self.household_repo = household_repo
        self.category_repo = category_repo
        self.member_repo = member_repo

    def create_budget(self, request: BudgetCreateRequest) -> BudgetModel:
        self.household_repo.get(request.household_id)
        if request.category_id:
            self.category_repo.get_for_household(category_id=request.category_id, household_id=request.household_id)
        if request.member_id:
            self.member_repo.get_for_household(member_id=request.member_id, household_id=request.household_id)
        return self.budget_repo.create(**request.model_dump())

    def get_budget_status(self, *, household_id: str, month: str, member_id: str | None = None) -> BudgetStatusRead:
        self.household_repo.get(household_id)
        budget_limit = self.budget_repo.total_limit(household_id=household_id, month=month, member_id=member_id)
        summary = self.transaction_repo.monthly_summary(household_id=household_id, month=month, member_id=member_id)
        spent = summary["expense"]
        remaining = budget_limit - spent
        ratio = float(spent / budget_limit) if budget_limit and budget_limit > Decimal("0") else 0.0
        return BudgetStatusRead(
            month=month,
            budget_limit=budget_limit,
            spent=spent,
            remaining=remaining,
            utilization_ratio=ratio,
        )
