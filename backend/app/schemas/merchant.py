from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MerchantBase(BaseModel):
    """Base merchant schema."""

    name: str = Field(..., min_length=1, max_length=255)
    business_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    email: EmailStr = Field(...)
    currency: str = Field(default="INR", min_length=3, max_length=3)


class MerchantCreate(MerchantBase):
    """Schema for creating a new merchant."""

    pass


class MerchantUpdate(BaseModel):
    """Schema for updating an existing merchant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class MerchantResponse(MerchantBase):
    """Response schema for merchant data."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
