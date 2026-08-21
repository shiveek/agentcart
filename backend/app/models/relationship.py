import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class ProductRelationship(Base):
    """ProductRelationship database model for cross-sell, upsell, and frequently bought together items."""

    __tablename__ = "product_relationships"

    __table_args__ = (
        UniqueConstraint(
            "source_product_id",
            "target_product_id",
            "relationship_type",
            name="uq_source_target_reltype",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # cross_sell, upsell, frequently_bought_together
    score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source_product: Mapped["Product"] = relationship(
        "Product",
        foreign_keys=[source_product_id],
        back_populates="source_relationships",
    )
    target_product: Mapped["Product"] = relationship(
        "Product",
        foreign_keys=[target_product_id],
        back_populates="target_relationships",
    )
