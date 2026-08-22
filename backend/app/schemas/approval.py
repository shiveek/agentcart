from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApprovalAction(BaseModel):
    """Schema for approving or rejecting an order."""

    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Schema for order approval status details."""

    id: UUID
    merchant_id: UUID
    order_id: UUID
    requested_amount: Decimal
    status: str
    reason: Optional[str] = None
    requested_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
