from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inventory import InventoryResponse


class ProductBase(BaseModel):
    """Base product schema."""

    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(...)
    category: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    is_active: bool = Field(default=True)


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    initial_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""

    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Response schema for product information."""

    id: UUID
    merchant_id: UUID
    created_at: datetime
    updated_at: datetime
    available_quantity: int = 0
    inventory: Optional[InventoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated list of products response schema."""

    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
