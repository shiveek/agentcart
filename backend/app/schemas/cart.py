from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartCreate(BaseModel):
    """Schema for creating a new cart."""

    customer_identifier: str = Field(..., description="Unique identifier for the buyer/customer")
    currency: str = Field(default="INR", max_length=3, description="3-letter currency code")


class CartItemCreate(BaseModel):
    """Schema for adding an item to a cart."""

    product_id: UUID = Field(..., description="Target product ID to add")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")


class CartItemUpdate(BaseModel):
    """Schema for updating item quantity in a cart."""

    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")


class CartItemResponse(BaseModel):
    """Schema for cart item response."""

    id: UUID
    cart_id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Schema for full cart response including items."""

    id: UUID
    merchant_id: UUID
    customer_identifier: str
    status: str
    currency: str
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CartSummaryResponse(BaseModel):
    """Schema for cart financial calculation summary."""

    cart_id: UUID
    items: List[CartItemResponse]
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    currency: str
