from decimal import Decimal
from pydantic import BaseModel, Field


class TransactionContext(BaseModel):
    """Pure domain object representing the context of a transaction to be evaluated by the Policy Engine."""

    amount: Decimal = Field(..., description="Total monetary transaction amount")
    discount_percent: Decimal = Field(default=Decimal("0.00"), description="Effective discount percentage applied")
    has_cross_sell: bool = Field(default=False, description="Whether transaction includes cross-sell items")
    has_upsell: bool = Field(default=False, description="Whether transaction includes upsell items")
    buyer_confirmation_provided: bool = Field(default=True, description="Whether buyer has explicitly confirmed the order")
    daily_spent: Decimal = Field(default=Decimal("0.00"), description="Buyer's accumulated spending today")
