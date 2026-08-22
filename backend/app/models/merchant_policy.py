import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class MerchantPolicy(Base):
    """Merchant Policy model governing transaction thresholds and sales rules."""

    __tablename__ = "merchant_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    max_transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("5000.00"), nullable=False
    )
    max_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("10.00"), nullable=False
    )
    approval_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("3000.00"), nullable=False
    )
    require_buyer_confirmation: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    allow_cross_sell: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    allow_upsell: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    max_payment_retries: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
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
