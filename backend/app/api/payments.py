import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_current_user
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.payment import (
    PaymentOrderResponse,
    PaymentResponse,
    PaymentRetryResponse,
    PaymentVerifyRequest,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/orders/{order_id}",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay Order for APPROVED internal order",
    description=(
        "Validates that the internal order is APPROVED, converts the order total from INR to integer paise, "
        "creates a Razorpay Order server-side, moves internal order state to PAYMENT_PENDING, "
        "and returns safe checkout data (Razorpay Order ID, Key ID, amount in paise)."
    ),
)
def create_payment_order_endpoint(
    order_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentOrderResponse:
    """Create payment order endpoint."""
    return payment_service.create_payment_order(
        db=db,
        merchant_id=current_merchant.id,
        order_id=order_id,
        actor_id=str(current_user.id),
    )


@router.post(
    "/verify",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify browser checkout payment callback signature",
    description=(
        "Verifies client-reported Razorpay checkout payment using HMAC-SHA256 and constant-time comparison. "
        "The provider_order_id is strictly fetched from the server DB using internal_order_id. "
        "Marks Payment CAPTURED and internal Order PAID."
    ),
)
def verify_payment_endpoint(
    request: PaymentVerifyRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Verify payment signature endpoint."""
    return payment_service.verify_checkout_payment(
        db=db,
        merchant_id=current_merchant.id,
        internal_order_id=request.internal_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
        actor_id=str(current_user.id),
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Payment details",
    description="Retrieves status and provider tracking information for a payment.",
)
def get_payment_endpoint(
    payment_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Get payment endpoint."""
    payment = payment_service.get_payment(db, current_merchant.id, payment_id)
    return PaymentResponse.model_validate(payment)


@router.post(
    "/orders/{order_id}/retry",
    response_model=PaymentRetryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry failed payment for an order",
    description=(
        "Initiates a new payment attempt for a PAYMENT_FAILED order if permitted by merchant policy max_payment_retries."
    ),
)
def retry_payment_endpoint(
    order_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRetryResponse:
    """Retry payment endpoint."""
    return payment_service.retry_payment(
        db=db,
        merchant_id=current_merchant.id,
        order_id=order_id,
        actor_id=str(current_user.id),
    )
