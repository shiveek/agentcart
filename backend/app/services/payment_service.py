import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.merchant import Merchant
from app.models.merchant_policy import MerchantPolicy
from app.models.order import Order
from app.models.payment import Payment, PaymentAttempt
from app.models.webhook_event import WebhookEvent
from app.schemas.payment import (
    PaymentOrderResponse,
    PaymentResponse,
    PaymentRetryResponse,
    WebhookResponse,
)
from app.services.audit_service import record_audit_event
from app.services.merchant_policy_service import get_merchant_policy
from app.services.razorpay_service import RazorpayService, razorpay_service

logger = logging.getLogger("agentcart.payment")


def _convert_decimal_to_paise(amount: Decimal) -> int:
    """Safely converts Decimal money value to integer paise without floating point inaccuracy."""
    return int(round(amount * Decimal("100.00")))


def create_payment_order(
    db: Session,
    merchant_id: uuid.UUID,
    order_id: uuid.UUID,
    actor_id: str,
    razorpay_svc: Optional[RazorpayService] = None,
) -> PaymentOrderResponse:
    """Creates a server-side Razorpay Order for an APPROVED internal order."""
    svc = razorpay_svc or razorpay_service

    # 1. Fetch internal order & verify merchant scoping
    order = db.execute(
        select(Order).where(Order.id == order_id, Order.merchant_id == merchant_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or does not belong to merchant",
        )

    # 2. Verify state is APPROVED (Reject BLOCKED, AWAITING_APPROVAL, CANCELLED, PAID)
    if order.status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid",
        )
    if order.status != "APPROVED" and order.status != "PAYMENT_PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only APPROVED orders may initiate payment. Current order status: '{order.status}'",
        )

    # 3. Idempotency Check: if payment already exists and has provider order ID
    existing_payment = db.execute(
        select(Payment).where(Payment.order_id == order_id)
    ).scalar_one_or_none()

    if existing_payment and existing_payment.provider_order_id:
        if existing_payment.status == "CAPTURED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already been captured for this order",
            )
        # Return existing payment order response idempotently
        paise_amount = _convert_decimal_to_paise(existing_payment.amount)
        return PaymentOrderResponse(
            internal_order_id=order.id,
            payment_id=existing_payment.id,
            razorpay_order_id=existing_payment.provider_order_id,
            razorpay_key_id=svc.key_id or settings.RAZORPAY_KEY_ID or "rzp_test_placeholder",
            amount=paise_amount,
            currency=existing_payment.currency,
        )

    # 4. Calculate exact amount in integer paise
    paise_amount = _convert_decimal_to_paise(order.total)
    receipt_id = f"receipt_{str(order.id)[:8]}"
    notes = {
        "internal_order_id": str(order.id),
        "merchant_id": str(merchant_id),
    }

    # 5. Create Razorpay order via service
    rzp_order = svc.create_order(
        amount_paise=paise_amount,
        currency=order.currency,
        receipt=receipt_id,
        notes=notes,
    )
    provider_order_id = rzp_order["id"]

    # 6. Create internal Payment record
    if not existing_payment:
        payment = Payment(
            merchant_id=merchant_id,
            order_id=order.id,
            provider="RAZORPAY",
            provider_order_id=provider_order_id,
            amount=order.total,
            currency=order.currency,
            status="CREATED",
        )
        db.add(payment)
    else:
        payment = existing_payment
        payment.provider_order_id = provider_order_id
        payment.status = "CREATED"

    # Move internal order to PAYMENT_PENDING
    order.status = "PAYMENT_PENDING"
    db.commit()
    db.refresh(payment)

    # Record initial payment attempt
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=1,
        status="CREATED",
    )
    db.add(attempt)
    db.commit()

    # 7. Audit log
    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="PAYMENT_ORDER_CREATED",
        resource_type="Payment",
        resource_id=str(payment.id),
        merchant_id=merchant_id,
        metadata={
            "order_id": str(order.id),
            "provider_order_id": provider_order_id,
            "amount_paise": paise_amount,
        },
    )

    key_id = svc.key_id or settings.RAZORPAY_KEY_ID or "rzp_test_placeholder"
    return PaymentOrderResponse(
        internal_order_id=order.id,
        payment_id=payment.id,
        razorpay_order_id=provider_order_id,
        razorpay_key_id=key_id,
        amount=paise_amount,
        currency=order.currency,
    )


def verify_checkout_payment(
    db: Session,
    merchant_id: uuid.UUID,
    internal_order_id: uuid.UUID,
    razorpay_payment_id: str,
    razorpay_signature: str,
    actor_id: str = "SYSTEM",
    razorpay_svc: Optional[RazorpayService] = None,
) -> PaymentResponse:
    """Verifies browser payment callback using DB-fetched provider_order_id and constant-time HMAC check."""
    svc = razorpay_svc or razorpay_service

    # Fetch Payment & Order from internal DB
    payment = db.execute(
        select(Payment).where(
            Payment.order_id == internal_order_id,
            Payment.merchant_id == merchant_id,
        )
    ).scalar_one_or_none()

    if not payment or not payment.provider_order_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found for internal order",
        )

    order = db.execute(
        select(Order).where(Order.id == internal_order_id)
    ).scalar_one_or_none()

    # Verify HMAC signature using server DB provider_order_id
    is_valid = svc.verify_payment_signature(
        provider_order_id=payment.provider_order_id,
        provider_payment_id=razorpay_payment_id,
        signature=razorpay_signature,
    )

    if not is_valid:
        record_audit_event(
            db=db,
            actor_type="USER",
            actor_id=actor_id,
            action="PAYMENT_SIGNATURE_REJECTED",
            resource_type="Payment",
            resource_id=str(payment.id),
            merchant_id=merchant_id,
            metadata={
                "order_id": str(internal_order_id),
                "razorpay_payment_id": razorpay_payment_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature",
        )

    # Signature is valid -> Mark Payment CAPTURED and Order PAID
    payment.status = "CAPTURED"
    payment.provider_payment_id = razorpay_payment_id
    payment.provider_signature = razorpay_signature
    payment.captured_at = datetime.now(timezone.utc)

    if order:
        order.status = "PAID"

    db.commit()
    db.refresh(payment)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="PAYMENT_SIGNATURE_VERIFIED",
        resource_type="Payment",
        resource_id=str(payment.id),
        merchant_id=merchant_id,
        metadata={"order_id": str(internal_order_id), "status": "CAPTURED"},
    )
    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="PAYMENT_CAPTURED",
        resource_type="Payment",
        resource_id=str(payment.id),
        merchant_id=merchant_id,
        metadata={"order_id": str(internal_order_id)},
    )

    return PaymentResponse.model_validate(payment)


def process_webhook_event(
    db: Session,
    raw_body: bytes,
    signature_header: str,
    razorpay_svc: Optional[RazorpayService] = None,
) -> WebhookResponse:
    """Idempotently processes Razorpay webhooks with raw body signature verification."""
    svc = razorpay_svc or razorpay_service

    # 1. Verify HMAC signature using RAZORPAY_WEBHOOK_SECRET
    is_valid = svc.verify_webhook_signature(raw_body, signature_header)
    if not is_valid:
        record_audit_event(
            db=db,
            actor_type="WEBHOOK",
            actor_id="RAZORPAY_WEBHOOK",
            action="WEBHOOK_SIGNATURE_REJECTED",
            resource_type="WebhookEvent",
            resource_id=None,
            metadata={"signature": signature_header},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    # 2. Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON in webhook body",
        )

    event_type = payload.get("event", "unknown")
    provider_event_id = payload.get("event_id") or payload.get("id") or hashlib.sha256(raw_body).hexdigest()

    # 3. Check for existing WebhookEvent for replay protection
    existing_event = db.execute(
        select(WebhookEvent).where(
            WebhookEvent.provider == "RAZORPAY",
            WebhookEvent.provider_event_id == provider_event_id,
        )
    ).scalar_one_or_none()

    if existing_event and existing_event.processed:
        record_audit_event(
            db=db,
            actor_type="WEBHOOK",
            actor_id="RAZORPAY_WEBHOOK",
            action="WEBHOOK_DUPLICATE",
            resource_type="WebhookEvent",
            resource_id=str(existing_event.id),
            metadata={"event_id": provider_event_id, "event_type": event_type},
        )
        return WebhookResponse(
            status="DUPLICATE",
            event_id=provider_event_id,
            event_type=event_type,
            processed=False,
        )

    # Store WebhookEvent
    if not existing_event:
        webhook_evt = WebhookEvent(
            provider="RAZORPAY",
            provider_event_id=provider_event_id,
            event_type=event_type,
            signature_verified=True,
            payload_json=payload,
            processed=True,
            processed_at=datetime.now(timezone.utc),
        )
        db.add(webhook_evt)
    else:
        webhook_evt = existing_event
        webhook_evt.processed = True
        webhook_evt.processed_at = datetime.now(timezone.utc)

    db.commit()

    # 4. Handle event types
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    provider_order_id = payment_entity.get("order_id")
    provider_payment_id = payment_entity.get("id")

    if provider_order_id or provider_payment_id:
        payment = db.execute(
            select(Payment).where(
                (Payment.provider_order_id == provider_order_id)
                | (Payment.provider_payment_id == provider_payment_id)
            )
        ).scalar_one_or_none()

        if payment:
            order = db.execute(select(Order).where(Order.id == payment.order_id)).scalar_one_or_none()

            if event_type == "payment.captured":
                payment.status = "CAPTURED"
                payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
                payment.method = payment_entity.get("method")
                payment.captured_at = datetime.now(timezone.utc)
                if order:
                    order.status = "PAID"
                db.commit()
                record_audit_event(
                    db=db,
                    actor_type="WEBHOOK",
                    actor_id="RAZORPAY_WEBHOOK",
                    action="PAYMENT_CAPTURED",
                    resource_type="Payment",
                    resource_id=str(payment.id),
                    merchant_id=payment.merchant_id,
                    metadata={"event_id": provider_event_id},
                )
            elif event_type == "payment.failed":
                payment.status = "FAILED"
                payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
                payment.error_code = payment_entity.get("error_code")
                payment.error_description = payment_entity.get("error_description")
                payment.failed_at = datetime.now(timezone.utc)
                if order:
                    order.status = "PAYMENT_FAILED"
                db.commit()
                record_audit_event(
                    db=db,
                    actor_type="WEBHOOK",
                    actor_id="RAZORPAY_WEBHOOK",
                    action="PAYMENT_FAILED",
                    resource_type="Payment",
                    resource_id=str(payment.id),
                    merchant_id=payment.merchant_id,
                    metadata={"event_id": provider_event_id, "error_code": payment.error_code},
                )

    record_audit_event(
        db=db,
        actor_type="WEBHOOK",
        actor_id="RAZORPAY_WEBHOOK",
        action="WEBHOOK_RECEIVED",
        resource_type="WebhookEvent",
        resource_id=str(webhook_evt.id),
        metadata={"event_id": provider_event_id, "event_type": event_type},
    )

    return WebhookResponse(
        status="SUCCESS",
        event_id=provider_event_id,
        event_type=event_type,
        processed=True,
    )


def retry_payment(
    db: Session,
    merchant_id: uuid.UUID,
    order_id: uuid.UUID,
    actor_id: str,
    razorpay_svc: Optional[RazorpayService] = None,
) -> PaymentRetryResponse:
    """Retries payment for a PAYMENT_FAILED order if permitted by merchant policy max_payment_retries."""
    order = db.execute(
        select(Order).where(Order.id == order_id, Order.merchant_id == merchant_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or does not belong to merchant",
        )

    if order.status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid",
        )

    if order.status != "PAYMENT_FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PAYMENT_FAILED orders may be retried. Current order status: '{order.status}'",
        )

    payment = db.execute(select(Payment).where(Payment.order_id == order.id)).scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record missing for order",
        )

    # Check merchant policy max_payment_retries
    m_policy = get_merchant_policy(db, merchant_id)
    max_retries = m_policy.max_payment_retries

    attempts_count = len(payment.attempts)
    if attempts_count >= (max_retries + 1):  # 1 initial attempt + max_retries
        record_audit_event(
            db=db,
            actor_type="USER",
            actor_id=actor_id,
            action="PAYMENT_RETRY_BLOCKED",
            resource_type="Payment",
            resource_id=str(payment.id),
            merchant_id=merchant_id,
            metadata={"attempts": attempts_count, "max_retries": max_retries},
        )
        return PaymentRetryResponse(
            status="RETRY_NOT_ALLOWED",
            reason=f"Maximum payment retry limit ({max_retries}) reached",
            payment_order=None,
        )

    # Create new attempt
    attempt_num = attempts_count + 1
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=attempt_num,
        status="RETRY_INITIATED",
    )
    db.add(attempt)
    order.status = "APPROVED"  # Reset status to APPROVED to allow payment order creation
    db.commit()

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="PAYMENT_RETRY_REQUESTED",
        resource_type="Payment",
        resource_id=str(payment.id),
        merchant_id=merchant_id,
        metadata={"attempt_number": attempt_num},
    )

    # Create new payment order
    payment_order = create_payment_order(
        db=db,
        merchant_id=merchant_id,
        order_id=order.id,
        actor_id=actor_id,
        razorpay_svc=razorpay_svc,
    )

    return PaymentRetryResponse(
        status="RETRY_INITIATED",
        reason=None,
        payment_order=payment_order,
    )


def get_payment(
    db: Session, merchant_id: uuid.UUID, payment_id: uuid.UUID
) -> Payment:
    """Retrieve Payment record by ID verifying merchant scoping."""
    payment = db.execute(
        select(Payment).where(
            Payment.id == payment_id, Payment.merchant_id == merchant_id
        )
    ).scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or does not belong to merchant",
        )
    return payment
