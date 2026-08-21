from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InventoryUpdate(BaseModel):
    """Schema for updating inventory level and reservations."""

    quantity: int = Field(..., ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_reservation_bounds(self) -> "InventoryUpdate":
        """Ensure reserved_quantity does not exceed total quantity."""
        if self.reserved_quantity > self.quantity:
            raise ValueError(
                f"reserved_quantity ({self.reserved_quantity}) cannot exceed total quantity ({self.quantity})"
            )
        return self


class InventoryResponse(BaseModel):
    """Response schema for product inventory details."""

    id: UUID
    product_id: UUID
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_level: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
