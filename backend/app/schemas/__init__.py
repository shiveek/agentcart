"""Schemas package module."""

from app.schemas.approval import ApprovalAction, ApprovalResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.schemas.buyer_policy import BuyerPolicyResponse, BuyerPolicyUpdate
from app.schemas.cart import (
    CartCreate,
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
    CartSummaryResponse,
)
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
from app.schemas.order import OrderItemResponse, OrderResponse
from app.schemas.payment import (
    PaymentOrderResponse,
    PaymentResponse,
    PaymentRetryResponse,
    PaymentVerifyRequest,
    WebhookResponse,
)
from app.schemas.policy import MerchantPolicyResponse, MerchantPolicyUpdate
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
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    "MerchantPolicyResponse",
    "MerchantPolicyUpdate",
    "BuyerPolicyResponse",
    "BuyerPolicyUpdate",
    "CartCreate",
    "CartItemCreate",
    "CartItemUpdate",
    "CartItemResponse",
    "CartResponse",
    "CartSummaryResponse",
    "OrderItemResponse",
    "OrderResponse",
    "ApprovalAction",
    "ApprovalResponse",
    "AuditLogResponse",
    "PaymentOrderResponse",
    "PaymentVerifyRequest",
    "PaymentResponse",
    "PaymentRetryResponse",
    "WebhookResponse",
]
