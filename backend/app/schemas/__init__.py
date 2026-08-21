"""Schemas package module."""

from app.schemas.catalog import (
    AICatalogAvailability,
    AICatalogCommerceAttributes,
    AICatalogMerchantSummary,
    AICatalogProductItem,
    AICatalogRelatedProduct,
    AICatalogResponse,
)
from app.schemas.health import HealthResponse
from app.schemas.inventory import InventoryResponse, InventoryUpdate
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.relationship import (
    ProductRelationshipCreate,
    ProductRelationshipResponse,
)

__all__ = [
    "HealthResponse",
    "MerchantCreate",
    "MerchantUpdate",
    "MerchantResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "InventoryUpdate",
    "InventoryResponse",
    "ProductRelationshipCreate",
    "ProductRelationshipResponse",
    "AICatalogMerchantSummary",
    "AICatalogAvailability",
    "AICatalogCommerceAttributes",
    "AICatalogRelatedProduct",
    "AICatalogProductItem",
    "AICatalogResponse",
]
