import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WebhookEvent(Base):
    """WebhookEvent model for tracking, verifying, and idempotently processing Razorpay webhooks."""

    __tablename__ = "webhook_events"

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_provider_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider: Mapped[str] = mapped_column(
        String(50), default="RAZORPAY", nullable=False, index=True
    )
    provider_event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    signature_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    payload_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    processed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
