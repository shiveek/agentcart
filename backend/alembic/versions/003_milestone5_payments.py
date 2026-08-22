"""Create milestone 5 payment tables: payments, payment_attempts, webhook_events

Revision ID: 003_milestone5_payments
Revises: 002_milestone3_tables
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_milestone5_payments"
down_revision: Union[str, None] = "002_milestone3_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="RAZORPAY"),
        sa.Column("provider_order_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("provider_signature", sa.String(length=512), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="CREATED"),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_order_id"),
        sa.UniqueConstraint("provider_payment_id"),
    )
    op.create_index(op.f("ix_payments_merchant_id"), "payments", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False)
    op.create_index(op.f("ix_payments_provider"), "payments", ["provider"], unique=False)
    op.create_index(op.f("ix_payments_provider_order_id"), "payments", ["provider_order_id"], unique=True)
    op.create_index(op.f("ix_payments_provider_payment_id"), "payments", ["provider_payment_id"], unique=True)
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)

    # 2. Create payment_attempts table
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_number"),
    )
    op.create_index(op.f("ix_payment_attempts_payment_id"), "payment_attempts", ["payment_id"], unique=False)

    # 3. Create webhook_events table
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="RAZORPAY"),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("payload_hash", sa.String(length=255), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_provider_event_id"),
    )
    op.create_index(op.f("ix_webhook_events_provider"), "webhook_events", ["provider"], unique=False)
    op.create_index(op.f("ix_webhook_events_provider_event_id"), "webhook_events", ["provider_event_id"], unique=False)
    op.create_index(op.f("ix_webhook_events_event_type"), "webhook_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_webhook_events_processed"), "webhook_events", ["processed"], unique=False)


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("payment_attempts")
    op.drop_table("payments")
