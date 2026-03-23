from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from domain.enums.account import AccountType
from domain.enums.identity import BindingRole, BindingStatus
from domain.enums.transaction import ImportJobStatus, TransactionDirection
from infra.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HouseholdModel(Base):
    __tablename__ = "households"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MemberModel(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_household_member", "household_id", "member_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    member_id: Mapped[str | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType))
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("household_id", "name", "parent_id", name="uq_categories_household_name_parent"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImportJobModel(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        Index("ix_import_jobs_household_status", "household_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    requested_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(100))
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    storage_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[ImportJobStatus] = mapped_column(Enum(ImportJobStatus), default=ImportJobStatus.PENDING)
    record_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_transactions_dedupe_key"),
        Index("ix_transactions_household_txn_time", "household_id", "txn_time"),
        Index("ix_transactions_household_member_txn_time", "household_id", "member_id", "txn_time"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    member_id: Mapped[str | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    import_job_id: Mapped[str | None] = mapped_column(ForeignKey("import_jobs.id"), nullable=True)
    direction: Mapped[TransactionDirection] = mapped_column(Enum(TransactionDirection))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    txn_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    dedupe_key: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(100), default="manual")
    source_txn_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BudgetModel(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("household_id", "month", "category_id", "member_id", name="uq_budgets_household_scope_month"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    month: Mapped[str] = mapped_column(String(7))
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    member_id: Mapped[str | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExternalIdentityBindingModel(Base):
    __tablename__ = "external_identity_bindings"
    __table_args__ = (
        UniqueConstraint("provider", "external_actor_id", "household_id", name="uq_bindings_provider_actor_household"),
        Index("ix_bindings_household_status", "household_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(100))
    external_actor_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    member_id: Mapped[str | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    role: Mapped[BindingRole] = mapped_column(Enum(BindingRole))
    status: Mapped[BindingStatus] = mapped_column(Enum(BindingStatus), default=BindingStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AgentAuditLogModel(Base):
    __tablename__ = "agent_audit_logs"
    __table_args__ = (
        Index("ix_agent_audit_logs_household_created", "household_id", "created_at"),
        Index("ix_agent_audit_logs_tool_idempotency", "tool_name", "household_id", "idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool_name: Mapped[str] = mapped_column(String(100))
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    member_id: Mapped[str | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    session_key: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    can_write: Mapped[bool] = mapped_column(Boolean)
    ok: Mapped[bool] = mapped_column(Boolean)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    args_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    args_preview: Mapped[str] = mapped_column(Text())
    result_preview: Mapped[str] = mapped_column(Text())
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
