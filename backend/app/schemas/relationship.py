from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductRelationshipCreate(BaseModel):
    """Schema for creating a product cross-sell/upsell relationship."""

    target_product_id: UUID
    relationship_type: str = Field(...)  # cross_sell, upsell, frequently_bought_together
    score: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("1.0"), decimal_places=2)
    reason: Optional[str] = None

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship_type(cls, value: str) -> str:
        """Ensure relationship type is one of the allowed values."""
        allowed = {"cross_sell", "upsell", "frequently_bought_together"}
        if value not in allowed:
            raise ValueError(
                f"relationship_type must be one of: {', '.join(sorted(allowed))}"
            )
        return value


class ProductRelationshipResponse(BaseModel):
    """Response schema for a product relationship."""

    id: UUID
    source_product_id: UUID
    target_product_id: UUID
    relationship_type: str
    score: Decimal
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
