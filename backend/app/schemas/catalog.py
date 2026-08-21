from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AICatalogMerchantSummary(BaseModel):
    """Merchant summary schema for AI catalog."""

    id: UUID
    name: str
    currency: str

    model_config = ConfigDict(from_attributes=True)


class AICatalogAvailability(BaseModel):
    """Stock availability details schema for AI buyer agent."""

    in_stock: bool
    available_quantity: int


class AICatalogCommerceAttributes(BaseModel):
    """Commerce flag attributes for AI buyer agent decisions."""

    can_recommend: bool = True
    can_cross_sell: bool = True


class AICatalogRelatedProduct(BaseModel):
    """Related product reference for AI recommendations."""

    target_product_id: UUID
    sku: str
    name: str
    price: Decimal
    relationship_type: str
    score: Decimal
    reason: Optional[str] = None


class AICatalogProductItem(BaseModel):
    """Structured product schema optimized for AI buyer agent consumption."""

    id: UUID
    sku: str
    name: str
    description: str
    category: str
    price: Decimal
    currency: str
    availability: AICatalogAvailability
    commerce_attributes: AICatalogCommerceAttributes
    related_products: List[AICatalogRelatedProduct] = Field(default_factory=list)


class AICatalogResponse(BaseModel):
    """Complete AI-readable catalog payload for a merchant."""

    merchant: AICatalogMerchantSummary
    products: List[AICatalogProductItem]
    total_count: int
