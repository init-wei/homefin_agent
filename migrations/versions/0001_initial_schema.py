"""Initial HomeFin schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-22 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "households",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("member_id", sa.String(length=36), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.Enum("CASH", "BANK", "CREDIT_CARD", "EWALLET", "ASSET", "LIABILITY", name="accounttype"), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("institution_name", sa.String(length=255), nullable=True),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_accounts_household_member", "accounts", ["household_id", "member_id"])
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=36), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("household_id", "name", "parent_id", name="uq_categories_household_name_parent"),
    )
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("account_id", sa.String(length=36), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("requested_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="importjobstatus"), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_import_jobs_household_status", "import_jobs", ["household_id", "status"])
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("account_id", sa.String(length=36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("member_id", sa.String(length=36), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("category_id", sa.String(length=36), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("import_job_id", sa.String(length=36), sa.ForeignKey("import_jobs.id"), nullable=True),
        sa.Column("direction", sa.Enum("INCOME", "EXPENSE", "TRANSFER_IN", "TRANSFER_OUT", name="transactiondirection"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("txn_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("counterparty", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_txn_id", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dedupe_key", name="uq_transactions_dedupe_key"),
    )
    op.create_index("ix_transactions_household_txn_time", "transactions", ["household_id", "txn_time"])
    op.create_index("ix_transactions_household_member_txn_time", "transactions", ["household_id", "member_id", "txn_time"])
    op.create_table(
        "budgets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("category_id", sa.String(length=36), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("member_id", sa.String(length=36), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("limit_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("household_id", "month", "category_id", "member_id", name="uq_budgets_household_scope_month"),
    )
    op.create_table(
        "external_identity_bindings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("external_actor_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("member_id", sa.String(length=36), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("role", sa.Enum("OWNER", "MEMBER", name="bindingrole"), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="bindingstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "external_actor_id", "household_id", name="uq_bindings_provider_actor_household"),
    )
    op.create_index("ix_bindings_household_status", "external_identity_bindings", ["household_id", "status"])
    op.create_table(
        "agent_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("member_id", sa.String(length=36), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("session_key", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("can_write", sa.Boolean(), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("args_payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("args_preview", sa.Text(), nullable=False),
        sa.Column("result_preview", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_audit_logs_household_created", "agent_audit_logs", ["household_id", "created_at"])
    op.create_index("ix_agent_audit_logs_tool_idempotency", "agent_audit_logs", ["tool_name", "household_id", "idempotency_key"])


def downgrade() -> None:
    op.drop_index("ix_agent_audit_logs_tool_idempotency", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_household_created", table_name="agent_audit_logs")
    op.drop_table("agent_audit_logs")
    op.drop_index("ix_bindings_household_status", table_name="external_identity_bindings")
    op.drop_table("external_identity_bindings")
    op.drop_table("budgets")
    op.drop_index("ix_transactions_household_member_txn_time", table_name="transactions")
    op.drop_index("ix_transactions_household_txn_time", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_import_jobs_household_status", table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_table("categories")
    op.drop_index("ix_accounts_household_member", table_name="accounts")
    op.drop_table("accounts")
    op.drop_table("members")
    op.drop_table("households")
    op.drop_table("users")
