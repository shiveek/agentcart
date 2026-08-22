import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentOrderResponse(BaseModel):
    """Schema for safe checkout configuration returned to frontend/client."""

    internal_order_id: uuid.UUID = Field(..., description="Internal AgentCart order UUID")
    payment_id: uuid.UUID = Field(..., description="Internal Payment UUID")
    razorpay_order_id: str = Field(..., description="Server-created Razorpay order ID (order_...)")
    razorpay_key_id: str = Field(..., description="Safe public Razorpay Key ID (rzp_test_...)")
    amount: int = Field(..., description="Transaction amount in smallest currency unit (e.g. paise for INR)")
    currency: str = Field(..., description="ISO 4217 Currency Code (e.g. INR)")

    model_config = ConfigDict(from_attributes=True)


class PaymentVerifyRequest(BaseModel):
    """Schema for client browser checkout verification callback."""

    internal_order_id: uuid.UUID = Field(..., description="Internal AgentCart order UUID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID reported by browser")
    razorpay_order_id: str = Field(..., description="Razorpay order ID reported by browser")
    razorpay_signature: str = Field(..., description="HMAC-SHA256 signature reported by browser")


class PaymentResponse(BaseModel):
    """Schema representing complete Payment record details."""

    id: uuid.UUID
    merchant_id: uuid.UUID
    order_id: uuid.UUID
    provider: str
    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    captured_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentRetryResponse(BaseModel):
    """Schema for payment retry operation response."""

    status: str = Field(..., description="Retry status (RETRY_INITIATED or RETRY_NOT_ALLOWED)")
    reason: Optional[str] = Field(default=None, description="Explanation if retry is blocked")
    payment_order: Optional[PaymentOrderResponse] = Field(default=None, description="New checkout configuration if retry succeeded")


class WebhookResponse(BaseModel):
    """Schema for webhook processing response."""

    status: str = Field(..., description="Webhook processing outcome (SUCCESS, DUPLICATE, REJECTED)")
    event_id: str = Field(..., description="Provider webhook event ID")
    event_type: str = Field(..., description="Provider event type")
    processed: bool = Field(..., description="Whether event was newly processed")
