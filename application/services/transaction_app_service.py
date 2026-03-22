from decimal import Decimal

from application.dto.transaction import (
    SharedExpenseUpdateRequest,
    TransactionCategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionSearchParams,
)
from application.services.errors import PermissionDenied, ValidationError
from domain.enums.transaction import TransactionDirection
from domain.value_objects.dedupe_key import build_dedupe_key
from infra.db.models import TransactionModel
from infra.db.repositories import AccountRepository, CategoryRepository, HouseholdRepository, MemberRepository, TransactionRepository


def apply_transaction_to_balance(*, current_balance: Decimal, direction: TransactionDirection, amount: Decimal) -> Decimal:
    if direction in {TransactionDirection.INCOME, TransactionDirection.TRANSFER_IN}:
        return current_balance + amount
    return current_balance - amount


class TransactionAppService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        category_repo: CategoryRepository,
        member_repo: MemberRepository,
        household_repo: HouseholdRepository,
    ) -> None:
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo
        self.category_repo = category_repo
        self.member_repo = member_repo
        self.household_repo = household_repo

    def create_manual_transaction(self, request: TransactionCreateRequest) -> TransactionModel:
        self.household_repo.get(request.household_id)
        account = self.account_repo.get_for_household(account_id=request.account_id, household_id=request.household_id)
        member_id = request.member_id
        if member_id:
            self.member_repo.get_for_household(member_id=member_id, household_id=request.household_id)
        if account.member_id:
            if member_id and member_id != account.member_id:
                raise ValidationError(
                    "account_member_mismatch",
                    f"Account {account.id} is scoped to member {account.member_id}, but transaction used member {member_id}.",
                )
            member_id = account.member_id
        if request.category_id:
            self.category_repo.get_for_household(category_id=request.category_id, household_id=request.household_id)
        dedupe_key = build_dedupe_key(
            household_id=request.household_id,
            account_id=request.account_id,
            txn_time=request.txn_time.isoformat(),
            amount=str(request.amount),
            counterparty=request.counterparty,
            description=request.description,
            source_txn_id=request.source_txn_id,
        )
        txn = self.transaction_repo.create(
            **request.model_dump(exclude={"idempotency_key", "member_id"}),
            member_id=member_id,
            dedupe_key=dedupe_key,
            raw_payload={"manual": True},
        )
        account.balance = apply_transaction_to_balance(
            current_balance=account.balance,
            direction=request.direction,
            amount=request.amount,
        )
        return txn

    def search_transactions(self, params: TransactionSearchParams) -> list[TransactionModel]:
        self.household_repo.get(params.household_id)
        if params.member_id:
            self.member_repo.get_for_household(member_id=params.member_id, household_id=params.household_id)
        if params.category_id:
            self.category_repo.get_for_household(category_id=params.category_id, household_id=params.household_id)
        if params.account_id:
            self.account_repo.get_for_household(account_id=params.account_id, household_id=params.household_id)
        return self.transaction_repo.search(**params.model_dump())

    def update_transaction_category(self, *, transaction_id: str, request: TransactionCategoryUpdateRequest) -> TransactionModel:
        txn = self.transaction_repo.get(transaction_id)
        self.category_repo.get_for_household(category_id=request.category_id, household_id=txn.household_id)
        txn.category_id = request.category_id
        return txn

    def mark_shared_expense(self, *, transaction_id: str, request: SharedExpenseUpdateRequest) -> TransactionModel:
        txn = self.transaction_repo.get(transaction_id)
        if txn.direction != TransactionDirection.EXPENSE:
            raise PermissionDenied("shared_expense_requires_expense", "Only expense transactions can be marked as shared.")
        txn.is_shared = request.is_shared
        return txn
