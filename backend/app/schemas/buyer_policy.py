from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BuyerPolicyResponse(BaseModel):
    """Schema representing AI buyer spending policy."""

    id: UUID
    customer_identifier: str
    max_transaction_amount: Decimal
    daily_spending_limit: Decimal
    require_confirmation_above: Decimal
    auto_pay_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuyerPolicyUpdate(BaseModel):
    """Schema for updating buyer spending policy."""

    max_transaction_amount: Optional[Decimal] = Field(None, gt=0)
    daily_spending_limit: Optional[Decimal] = Field(None, gt=0)
    require_confirmation_above: Optional[Decimal] = Field(None, gt=0)
    auto_pay_enabled: Optional[bool] = None
