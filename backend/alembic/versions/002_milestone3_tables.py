"""Create milestone 3 tables: users, merchant_policies, buyer_policies, carts, cart_items, orders, order_items, approvals, audit_logs

Revision ID: 002_milestone3_tables
Revises: 001_create_commerce_tables
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_milestone3_tables"
down_revision: Union[str, None] = "001_create_commerce_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="merchant_admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_merchant_id"), "users", ["merchant_id"], unique=False)

    # 2. Create merchant_policies table
    op.create_table(
        "merchant_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("max_transaction_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="5000.00"),
        sa.Column("max_discount_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="10.00"),
        sa.Column("approval_threshold", sa.Numeric(precision=12, scale=2), nullable=False, server_default="3000.00"),
        sa.Column("require_buyer_confirmation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_cross_sell", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_upsell", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_payment_retries", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id"),
    )
    op.create_index(op.f("ix_merchant_policies_merchant_id"), "merchant_policies", ["merchant_id"], unique=True)

    # 3. Create buyer_policies table
    op.create_table(
        "buyer_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("customer_identifier", sa.String(length=100), nullable=False),
        sa.Column("max_transaction_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="5000.00"),
        sa.Column("daily_spending_limit", sa.Numeric(precision=12, scale=2), nullable=False, server_default="10000.00"),
        sa.Column("require_confirmation_above", sa.Numeric(precision=12, scale=2), nullable=False, server_default="2000.00"),
        sa.Column("auto_pay_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "customer_identifier", name="uq_merchant_customer_identifier"),
    )
    op.create_index(op.f("ix_buyer_policies_merchant_id"), "buyer_policies", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_buyer_policies_customer_identifier"), "buyer_policies", ["customer_identifier"], unique=False)

    # 4. Create carts table
    op.create_table(
        "carts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("customer_identifier", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_carts_merchant_id"), "carts", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_carts_customer_identifier"), "carts", ["customer_identifier"], unique=False)
    op.create_index(op.f("ix_carts_status"), "carts", ["status"], unique=False)

    # 5. Create cart_items table
    op.create_table(
        "cart_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cart_items_cart_id"), "cart_items", ["cart_id"], unique=False)
    op.create_index(op.f("ix_cart_items_product_id"), "cart_items", ["product_id"], unique=False)

    # 6. Create orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("customer_identifier", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_total", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("tax_total", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("policy_status", sa.String(length=50), nullable=False, server_default="NOT_CHECKED"),
        sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "idempotency_key", name="uq_merchant_idempotency"),
    )
    op.create_index(op.f("ix_orders_merchant_id"), "orders", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_orders_cart_id"), "orders", ["cart_id"], unique=False)
    op.create_index(op.f("ix_orders_customer_identifier"), "orders", ["customer_identifier"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(op.f("ix_orders_idempotency_key"), "orders", ["idempotency_key"], unique=False)

    # 7. Create order_items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("product_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("sku_snapshot", sa.String(length=100), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)

    # 8. Create approvals table
    op.create_table(
        "approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("requested_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(op.f("ix_approvals_merchant_id"), "approvals", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_approvals_order_id"), "approvals", ["order_id"], unique=True)
    op.create_index(op.f("ix_approvals_status"), "approvals", ["status"], unique=False)

    # 9. Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=True),
        sa.Column("actor_type", sa.String(length=50), nullable=False, server_default="USER"),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("policy_decision", sa.String(length=50), nullable=True),
        sa.Column("approval_status", sa.String(length=50), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_merchant_id"), "audit_logs", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_type"), "audit_logs", ["actor_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("approvals")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("buyer_policies")
    op.drop_table("merchant_policies")
    op.drop_table("users")
