from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MerchantPolicyResponse(BaseModel):
    """Schema representing merchant policy configuration."""

    id: UUID
    merchant_id: UUID
    max_transaction_amount: Decimal
    max_discount_percent: Decimal
    approval_threshold: Decimal
    require_buyer_confirmation: bool
    allow_cross_sell: bool
    allow_upsell: bool
    max_payment_retries: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MerchantPolicyUpdate(BaseModel):
    """Schema for updating merchant policy configuration with strict validation rules."""

    max_transaction_amount: Optional[Decimal] = Field(
        None, gt=0, description="Maximum allowed single transaction amount (> 0)"
    )
    max_discount_percent: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Maximum allowed discount percentage (0 to 100)"
    )
    approval_threshold: Optional[Decimal] = Field(
        None, gt=0, description="Threshold above which approval is required (> 0)"
    )
    require_buyer_confirmation: Optional[bool] = None
    allow_cross_sell: Optional[bool] = None
    allow_upsell: Optional[bool] = None
    max_payment_retries: Optional[int] = Field(
        None, ge=0, description="Maximum allowed payment retry attempts (>= 0)"
    )

    @model_validator(mode="after")
    def validate_approval_threshold(self) -> "MerchantPolicyUpdate":
        """Ensure approval_threshold <= max_transaction_amount if both are provided."""
        if (
            self.approval_threshold is not None
            and self.max_transaction_amount is not None
            and self.approval_threshold > self.max_transaction_amount
        ):
            raise ValueError(
                "approval_threshold cannot exceed max_transaction_amount"
            )
        return self
