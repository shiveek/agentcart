from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    """Schema for item snapshot in an order."""

    id: UUID
    order_id: UUID
    product_id: UUID
    product_name_snapshot: str
    sku_snapshot: str
    unit_price: Decimal
    quantity: int
    discount_amount: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Schema for order response."""

    id: UUID
    merchant_id: UUID
    cart_id: UUID
    customer_identifier: str
    status: str
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    policy_status: str
    approval_status: str
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    violations: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
