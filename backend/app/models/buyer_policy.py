import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class BuyerPolicy(Base):
    """Buyer Policy database model representing merchant-scoped spending rules for AI buyers."""

    __tablename__ = "buyer_policies"

    __table_args__ = (
        UniqueConstraint(
            "merchant_id", "customer_identifier", name="uq_merchant_customer_identifier"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_identifier: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    max_transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("5000.00"), nullable=False
    )
    daily_spending_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("10000.00"), nullable=False
    )
    require_confirmation_above: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("2000.00"), nullable=False
    )
    auto_pay_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant")
