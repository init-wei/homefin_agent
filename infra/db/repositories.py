from __future__ import annotations

import json
from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from application.services.errors import NotFoundError, ValidationError
from domain.entities.contracts import ExternalIdentityBinding
from domain.enums.identity import BindingStatus
from domain.enums.transaction import ImportJobStatus, TransactionDirection
from infra.db.models import (
    AccountModel,
    AgentAuditLogModel,
    BudgetModel,
    CategoryModel,
    ExternalIdentityBindingModel,
    HouseholdModel,
    ImportJobModel,
    MemberModel,
    TransactionModel,
    UserModel,
)


def month_bounds(month: str) -> tuple[datetime, datetime]:
    year, month_num = [int(part) for part in month.split("-", maxsplit=1)]
    start = datetime(year, month_num, 1, tzinfo=timezone.utc)
    end = datetime(year, month_num, monthrange(year, month_num)[1], 23, 59, 59, 999999, tzinfo=timezone.utc)
    return start, end


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, email: str, display_name: str, password_hash: str | None) -> UserModel:
        if self.get_by_email(email):
            raise ValidationError("user_email_exists", f"A user with email {email} already exists.")
        user = UserModel(email=email, display_name=display_name, password_hash=password_hash)
        self.session.add(user)
        self.session.flush()
        return user

    def get_or_create(self, *, email: str, display_name: str) -> UserModel:
        user = self.session.scalar(select(UserModel).where(UserModel.email == email))
        if user:
            user.display_name = display_name
            return user
        user = UserModel(email=email, display_name=display_name, password_hash=None)
        self.session.add(user)
        self.session.flush()
        return user

    def get(self, user_id: str) -> UserModel:
        user = self.session.get(UserModel, user_id)
        if not user:
            raise NotFoundError("user_not_found", f"User {user_id} was not found.")
        return user

    def get_by_email(self, email: str) -> UserModel | None:
        return self.session.scalar(select(UserModel).where(UserModel.email == email))


class HouseholdRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, name: str, owner_user_id: str) -> HouseholdModel:
        household = HouseholdModel(name=name, owner_user_id=owner_user_id)
        self.session.add(household)
        self.session.flush()
        return household

    def get(self, household_id: str) -> HouseholdModel:
        household = self.session.get(HouseholdModel, household_id)
        if not household:
            raise NotFoundError("household_not_found", f"Household {household_id} was not found.")
        return household

    def assert_owner(self, *, household_id: str, user_id: str) -> HouseholdModel:
        household = self.get(household_id)
        if household.owner_user_id != user_id:
            raise ValidationError("owner_required", f"User {user_id} is not the owner of household {household_id}.")
        return household


class MemberRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, household_id: str, user_id: str | None, name: str, role: str = "member") -> MemberModel:
        member = MemberModel(household_id=household_id, user_id=user_id, name=name, role=role)
        self.session.add(member)
        self.session.flush()
        return member

    def get(self, member_id: str) -> MemberModel:
        member = self.session.get(MemberModel, member_id)
        if not member:
            raise NotFoundError("member_not_found", f"Member {member_id} was not found.")
        return member

    def get_for_household(self, *, member_id: str, household_id: str) -> MemberModel:
        member = self.get(member_id)
        if member.household_id != household_id:
            raise ValidationError("member_household_mismatch", f"Member {member_id} does not belong to household {household_id}.")
        return member

    def find_by_user_and_household(self, *, user_id: str, household_id: str) -> MemberModel | None:
        stmt = select(MemberModel).where(
            MemberModel.user_id == user_id,
            MemberModel.household_id == household_id,
        )
        return self.session.scalar(stmt)


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **kwargs: Any) -> AccountModel:
        account = AccountModel(**kwargs)
        self.session.add(account)
        self.session.flush()
        return account

    def list_by_household(self, household_id: str, member_id: str | None = None) -> list[AccountModel]:
        stmt = select(AccountModel).where(AccountModel.household_id == household_id)
        if member_id:
            stmt = stmt.where((AccountModel.member_id == member_id) | (AccountModel.member_id.is_(None)))
        return list(self.session.scalars(stmt.order_by(AccountModel.created_at.desc())))

    def get(self, account_id: str) -> AccountModel:
        account = self.session.get(AccountModel, account_id)
        if not account:
            raise NotFoundError("account_not_found", f"Account {account_id} was not found.")
        return account

    def get_for_household(self, *, account_id: str, household_id: str) -> AccountModel:
        account = self.get(account_id)
        if account.household_id != household_id:
            raise ValidationError("account_household_mismatch", f"Account {account_id} does not belong to household {household_id}.")
        return account


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **kwargs: Any) -> CategoryModel:
        category = CategoryModel(**kwargs)
        self.session.add(category)
        self.session.flush()
        return category

    def list_by_household(self, household_id: str) -> list[CategoryModel]:
        stmt = select(CategoryModel).where(CategoryModel.household_id == household_id).order_by(CategoryModel.name.asc())
        return list(self.session.scalars(stmt))

    def get(self, category_id: str) -> CategoryModel:
        category = self.session.get(CategoryModel, category_id)
        if not category:
            raise NotFoundError("category_not_found", f"Category {category_id} was not found.")
        return category

    def get_for_household(self, *, category_id: str, household_id: str) -> CategoryModel:
        category = self.get(category_id)
        if category.household_id != household_id:
            raise ValidationError("category_household_mismatch", f"Category {category_id} does not belong to household {household_id}.")
        return category


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **kwargs: Any) -> TransactionModel:
        txn = TransactionModel(**kwargs)
        self.session.add(txn)
        self.session.flush()
        return txn

    def get(self, transaction_id: str) -> TransactionModel:
        txn = self.session.get(TransactionModel, transaction_id)
        if not txn:
            raise NotFoundError("transaction_not_found", f"Transaction {transaction_id} was not found.")
        return txn

    def get_for_household(self, *, transaction_id: str, household_id: str) -> TransactionModel:
        txn = self.get(transaction_id)
        if txn.household_id != household_id:
            raise ValidationError("transaction_household_mismatch", f"Transaction {transaction_id} does not belong to household {household_id}.")
        return txn

    def dedupe_exists(self, dedupe_key: str) -> bool:
        stmt = select(TransactionModel.id).where(TransactionModel.dedupe_key == dedupe_key).limit(1)
        return self.session.scalar(stmt) is not None

    def search(
        self,
        *,
        household_id: str,
        month: str | None,
        member_id: str | None,
        category_id: str | None,
        account_id: str | None,
        limit: int,
    ) -> list[TransactionModel]:
        stmt = select(TransactionModel).where(TransactionModel.household_id == household_id)
        if month:
            start, end = month_bounds(month)
            stmt = stmt.where(TransactionModel.txn_time >= start, TransactionModel.txn_time <= end)
        if member_id:
            stmt = stmt.where(TransactionModel.member_id == member_id)
        if category_id:
            stmt = stmt.where(TransactionModel.category_id == category_id)
        if account_id:
            stmt = stmt.where(TransactionModel.account_id == account_id)
        stmt = stmt.order_by(TransactionModel.txn_time.desc()).limit(limit)
        return list(self.session.scalars(stmt))

    def monthly_summary(self, *, household_id: str, month: str, member_id: str | None) -> dict[str, Any]:
        start, end = month_bounds(month)
        income_case = case(
            (TransactionModel.direction.in_([TransactionDirection.INCOME, TransactionDirection.TRANSFER_IN]), TransactionModel.amount),
            else_=Decimal("0"),
        )
        expense_case = case(
            (TransactionModel.direction.in_([TransactionDirection.EXPENSE, TransactionDirection.TRANSFER_OUT]), TransactionModel.amount),
            else_=Decimal("0"),
        )
        stmt = select(
            func.coalesce(func.sum(income_case), Decimal("0")),
            func.coalesce(func.sum(expense_case), Decimal("0")),
            func.count(TransactionModel.id),
        ).where(
            TransactionModel.household_id == household_id,
            TransactionModel.txn_time >= start,
            TransactionModel.txn_time <= end,
        )
        if member_id:
            stmt = stmt.where(TransactionModel.member_id == member_id)
        income, expense, count = self.session.execute(stmt).one()
        return {
            "month": month,
            "income": income,
            "expense": expense,
            "net": income - expense,
            "transaction_count": count,
        }

    def category_breakdown(self, *, household_id: str, month: str, member_id: str | None) -> list[dict[str, Any]]:
        start, end = month_bounds(month)
        label = func.coalesce(CategoryModel.name, "Uncategorized")
        stmt = (
            select(label, func.coalesce(func.sum(TransactionModel.amount), Decimal("0")))
            .select_from(TransactionModel)
            .outerjoin(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                TransactionModel.household_id == household_id,
                TransactionModel.direction == TransactionDirection.EXPENSE,
                TransactionModel.txn_time >= start,
                TransactionModel.txn_time <= end,
            )
            .group_by(label)
            .order_by(func.sum(TransactionModel.amount).desc())
        )
        if member_id:
            stmt = stmt.where(TransactionModel.member_id == member_id)
        return [{"category": category, "total": total} for category, total in self.session.execute(stmt).all()]

    def member_spending(self, *, household_id: str, month: str, member_id: str | None) -> list[dict[str, Any]]:
        start, end = month_bounds(month)
        stmt = (
            select(
                func.coalesce(MemberModel.id, "unassigned"),
                func.coalesce(MemberModel.name, "Unassigned"),
                func.coalesce(func.sum(TransactionModel.amount), Decimal("0")),
            )
            .select_from(TransactionModel)
            .outerjoin(MemberModel, TransactionModel.member_id == MemberModel.id)
            .where(
                TransactionModel.household_id == household_id,
                TransactionModel.direction == TransactionDirection.EXPENSE,
                TransactionModel.txn_time >= start,
                TransactionModel.txn_time <= end,
            )
            .group_by(MemberModel.id, MemberModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
        )
        if member_id:
            stmt = stmt.where(TransactionModel.member_id == member_id)
        rows = self.session.execute(stmt).all()
        return [{"member_id": member_id_value, "member_name": name, "total": total} for member_id_value, name, total in rows]


class ImportJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **kwargs: Any) -> ImportJobModel:
        job = ImportJobModel(**kwargs)
        self.session.add(job)
        self.session.flush()
        return job

    def get(self, job_id: str) -> ImportJobModel:
        job = self.session.get(ImportJobModel, job_id)
        if not job:
            raise NotFoundError("import_job_not_found", f"Import job {job_id} was not found.")
        return job

    def get_for_household(self, *, job_id: str, household_id: str) -> ImportJobModel:
        job = self.get(job_id)
        if job.household_id != household_id:
            raise ValidationError("import_job_household_mismatch", f"Import job {job_id} does not belong to household {household_id}.")
        return job

    def list_pending(self, *, limit: int = 20) -> list[ImportJobModel]:
        stmt = (
            select(ImportJobModel)
            .where(ImportJobModel.status == ImportJobStatus.PENDING)
            .order_by(ImportJobModel.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def set_status(
        self,
        job: ImportJobModel,
        *,
        status: ImportJobStatus,
        record_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        job.status = status
        if record_count is not None:
            job.record_count = record_count
        job.error_message = error_message
        self.session.flush()


class BudgetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **kwargs: Any) -> BudgetModel:
        budget = BudgetModel(**kwargs)
        self.session.add(budget)
        self.session.flush()
        return budget

    def total_limit(self, *, household_id: str, month: str, member_id: str | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(BudgetModel.limit_amount), Decimal("0"))).where(
            BudgetModel.household_id == household_id,
            BudgetModel.month == month,
        )
        if member_id:
            stmt = stmt.where((BudgetModel.member_id == member_id) | (BudgetModel.member_id.is_(None)))
        return self.session.scalar(stmt) or Decimal("0")


class BindingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, binding: ExternalIdentityBinding) -> ExternalIdentityBindingModel:
        model = ExternalIdentityBindingModel(
            provider=binding.provider,
            external_actor_id=binding.external_actor_id,
            user_id=binding.user_id,
            member_id=binding.member_id,
            household_id=binding.household_id,
            role=binding.role,
            status=binding.status,
        )
        self.session.add(model)
        self.session.flush()
        return model

    def find_conflict(self, *, provider: str, external_actor_id: str, household_id: str) -> ExternalIdentityBindingModel | None:
        stmt = select(ExternalIdentityBindingModel).where(
            ExternalIdentityBindingModel.provider == provider,
            ExternalIdentityBindingModel.external_actor_id == external_actor_id,
            ExternalIdentityBindingModel.household_id == household_id,
        )
        return self.session.scalar(stmt)

    def find_active(self, *, provider: str, external_actor_id: str, household_id: str) -> ExternalIdentityBindingModel | None:
        stmt = select(ExternalIdentityBindingModel).where(
            ExternalIdentityBindingModel.provider == provider,
            ExternalIdentityBindingModel.external_actor_id == external_actor_id,
            ExternalIdentityBindingModel.household_id == household_id,
            ExternalIdentityBindingModel.status == BindingStatus.ACTIVE,
        )
        return self.session.scalar(stmt)


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        tool_name: str,
        household_id: str,
        user_id: str | None,
        member_id: str | None,
        session_key: str,
        role: str,
        can_write: bool,
        ok: bool,
        error_code: str | None,
        args_payload: dict[str, Any],
        result_payload: dict[str, Any],
        idempotency_key: str | None,
    ) -> AgentAuditLogModel:
        safe_args = json.loads(json.dumps(args_payload, default=str))
        safe_result = json.loads(json.dumps(result_payload, default=str))
        log = AgentAuditLogModel(
            tool_name=tool_name,
            household_id=household_id,
            user_id=user_id,
            member_id=member_id,
            session_key=session_key,
            role=role,
            can_write=can_write,
            ok=ok,
            error_code=error_code,
            args_payload=safe_args,
            result_payload=safe_result,
            args_preview=json.dumps(safe_args, ensure_ascii=True)[:500],
            result_preview=json.dumps(safe_result, ensure_ascii=True)[:500],
            idempotency_key=idempotency_key,
        )
        self.session.add(log)
        self.session.flush()
        return log

    def find_success_by_idempotency(
        self,
        *,
        tool_name: str,
        household_id: str,
        user_id: str | None,
        idempotency_key: str,
    ) -> AgentAuditLogModel | None:
        stmt = (
            select(AgentAuditLogModel)
            .where(
                AgentAuditLogModel.tool_name == tool_name,
                AgentAuditLogModel.household_id == household_id,
                AgentAuditLogModel.user_id == user_id,
                AgentAuditLogModel.idempotency_key == idempotency_key,
                AgentAuditLogModel.ok.is_(True),
            )
            .order_by(AgentAuditLogModel.created_at.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_recent(self, *, household_id: str, limit: int = 50) -> list[AgentAuditLogModel]:
        stmt = (
            select(AgentAuditLogModel)
            .where(AgentAuditLogModel.household_id == household_id)
            .order_by(AgentAuditLogModel.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
