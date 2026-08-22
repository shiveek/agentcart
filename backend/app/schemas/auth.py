from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    role: str = Field(
        default="merchant_admin",
        pattern="^(merchant_admin|merchant_staff)$",
        description="Role must be merchant_admin or merchant_staff",
    )
    merchant_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """Schema for user authentication/login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user details output."""

    id: UUID
    merchant_id: Optional[UUID] = None
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
