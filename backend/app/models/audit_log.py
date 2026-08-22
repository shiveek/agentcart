import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class AuditLog(Base):
    """AuditLog database model for tracking system, security, and policy events."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="USER", index=True
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_decision: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant")
