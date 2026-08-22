import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.product import ProductCreate
from app.services import (
    merchant_policy_service,
    order_service,
    product_service,
)
from app.services.razorpay_service import RazorpayService


class FakeRazorpayService(RazorpayService):
    """Fake RazorpayService for testing without live API network calls."""

    def __init__(self):
        super().__init__(
            key_id="rzp_test_fake12345",
            key_secret="fake_key_secret_12345",
            webhook_secret="fake_webhook_secret_12345",
        )

    def create_order(
        self,
        amount_paise: int,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "id": f"order_fake_{uuid.uuid4().hex[:10]}",
            "entity": "order",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "notes": notes or {},
        }

    def verify_payment_signature(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> bool:
        msg = f"{provider_order_id}|{provider_payment_id}"
        expected = hmac.new(
            self.key_secret.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature_header: str,
    ) -> bool:
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)


def _setup_approved_order(client: TestClient, db: Session):
    """Helper to set up a merchant, user, product, cart, and APPROVED internal order."""
    unique_email = f"pay_merchant_{uuid.uuid4().hex[:8]}@example.com"
    m_res = client.post("/api/merchants", json={
        "name": "Payment Test Store",
        "business_name": "Pay Ltd",
        "email": unique_email,
        "currency": "INR",
    })
    merchant_id = uuid.UUID(m_res.json()["id"])

    # Register & Login User
    client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(merchant_id),
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set up Merchant Policy
    m_policy = merchant_policy_service.get_merchant_policy(db, merchant_id)
    m_policy.max_transaction_amount = Decimal("10000.00")
    m_policy.approval_threshold = Decimal("8000.00")
    m_policy.max_payment_retries = 2
    db.commit()

    # Create Product
    product = product_service.create_product(
        db,
        merchant_id,
        ProductCreate(
            sku=f"PAY-PROD-{uuid.uuid4().hex[:4]}",
            name="Payment Spec Item",
            description="Item for payment testing",
            category="Gadgets",
            price=Decimal("2500.00"),
            currency="INR",
            initial_quantity=50,
        ),
    )

    # Create Cart & Add Item with Auth Headers
    cart_res = client.post("/api/carts", json={"customer_identifier": "pay-buyer-001"}, headers=headers)
    cart_id = uuid.UUID(cart_res.json()["id"])

    client.post(f"/api/carts/{cart_id}/items", json={
        "product_id": str(product.id),
        "quantity": 1,
    }, headers=headers)

    # Checkout Cart -> Order
    order_res = client.post(f"/api/orders/from-cart/{cart_id}", headers=headers)
    order_id = uuid.UUID(order_res.json()["id"])

    # Verify Order is APPROVED
    db_order = db.get(Order, order_id)
    assert db_order.status == "APPROVED"

    return merchant_id, order_id, headers, token


def test_payment_creation_and_paise_conversion(client: TestClient, db: Session, monkeypatch):
    """Test Razorpay order creation for APPROVED internal order and exact paise conversion."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)
    fake_svc = FakeRazorpayService()

    from app.services import payment_service
    monkeypatch.setattr(payment_service, "razorpay_service", fake_svc)

    res = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["internal_order_id"] == str(order_id)
    assert data["razorpay_order_id"].startswith("order_fake_")
    assert data["amount"] == 250000  # ₹2500.00 -> 250000 paise
    assert data["currency"] == "INR"

    # Check internal DB state
    db_order = db.get(Order, order_id)
    assert db_order.status == "PAYMENT_PENDING"


def test_payment_creation_idempotency(client: TestClient, db: Session, monkeypatch):
    """Test duplicate payment creation requests return existing provider order without duplicates."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)
    fake_svc = FakeRazorpayService()

    from app.services import payment_service
    monkeypatch.setattr(payment_service, "razorpay_service", fake_svc)

    res1 = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    assert res1.status_code == 201
    rzp_id_1 = res1.json()["razorpay_order_id"]

    # Second call for same order
    res2 = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    assert res2.status_code == 201
    rzp_id_2 = res2.json()["razorpay_order_id"]

    assert rzp_id_1 == rzp_id_2


def test_reject_unapproved_order_payment(client: TestClient, db: Session):
    """Test payment creation fails if internal order status is not APPROVED."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)

    # Change order status to CANCELLED
    db_order = db.get(Order, order_id)
    db_order.status = "CANCELLED"
    db.commit()

    res = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    assert res.status_code == 400
    assert "Only APPROVED orders may initiate payment" in res.json()["detail"]


def test_payment_signature_verification_success_and_failure(client: TestClient, db: Session, monkeypatch):
    """Test HMAC payment signature verification success and failure handling."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)
    fake_svc = FakeRazorpayService()

    from app.services import payment_service
    monkeypatch.setattr(payment_service, "razorpay_service", fake_svc)

    # 1. Create Payment Order
    create_res = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    provider_order_id = create_res.json()["razorpay_order_id"]
    fake_payment_id = "pay_fake_12345"

    # 2. Invalid Signature -> REJECTED
    bad_verify = client.post("/api/payments/verify", json={
        "internal_order_id": str(order_id),
        "razorpay_payment_id": fake_payment_id,
        "razorpay_order_id": provider_order_id,
        "razorpay_signature": "invalid_signature_hash",
    }, headers=headers)
    assert bad_verify.status_code == 400
    assert "Invalid payment signature" in bad_verify.json()["detail"]

    # 3. Valid Signature -> PAID
    msg = f"{provider_order_id}|{fake_payment_id}"
    valid_signature = hmac.new(
        fake_svc.key_secret.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    good_verify = client.post("/api/payments/verify", json={
        "internal_order_id": str(order_id),
        "razorpay_payment_id": fake_payment_id,
        "razorpay_order_id": provider_order_id,
        "razorpay_signature": valid_signature,
    }, headers=headers)

    assert good_verify.status_code == 200
    assert good_verify.json()["status"] == "CAPTURED"

    # Internal Order becomes PAID
    db_order = db.get(Order, order_id)
    assert db_order.status == "PAID"


def test_razorpay_webhook_processing_and_idempotency(client: TestClient, db: Session, monkeypatch):
    """Test webhook verification, state update, and duplicate event replay protection."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)
    fake_svc = FakeRazorpayService()

    from app.services import payment_service
    from app.api import webhooks
    monkeypatch.setattr(payment_service, "razorpay_service", fake_svc)

    create_res = client.post(f"/api/payments/orders/{order_id}", headers=headers)
    provider_order_id = create_res.json()["razorpay_order_id"]

    # Construct Webhook Payload for payment.captured
    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "event": "payment.captured",
        "event_id": event_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_wh_12345",
                    "order_id": provider_order_id,
                    "method": "card",
                    "amount": 250000,
                }
            }
        }
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    valid_sig = hmac.new(
        fake_svc.webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    # 1. Process Webhook
    res = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"
    assert res.json()["processed"] is True

    # Check DB state -> PAID
    db_order = db.get(Order, order_id)
    assert db_order.status == "PAID"

    # 2. Duplicate Webhook Event -> DUPLICATE response
    dup_res = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["status"] == "DUPLICATE"
    assert dup_res.json()["processed"] is False


def test_payment_retry_flow(client: TestClient, db: Session, monkeypatch):
    """Test retrying PAYMENT_FAILED order up to max_payment_retries limit."""
    merchant_id, order_id, headers, _ = _setup_approved_order(client, db)
    fake_svc = FakeRazorpayService()

    from app.services import payment_service
    monkeypatch.setattr(payment_service, "razorpay_service", fake_svc)

    # Initiate first payment
    client.post(f"/api/payments/orders/{order_id}", headers=headers)

    # Simulate payment failure via webhook
    db_payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    db_payment.status = "FAILED"
    db_order = db.get(Order, order_id)
    db_order.status = "PAYMENT_FAILED"
    db.commit()

    # 1. Retry Attempt 1 -> SUCCESS
    retry1 = client.post(f"/api/payments/orders/{order_id}/retry", headers=headers)
    assert retry1.status_code == 200
    assert retry1.json()["status"] == "RETRY_INITIATED"

    # Simulate failure on attempt 2
    db_payment.status = "FAILED"
    db_order.status = "PAYMENT_FAILED"
    db.commit()

    # 2. Retry Attempt 2 -> SUCCESS
    retry2 = client.post(f"/api/payments/orders/{order_id}/retry", headers=headers)
    assert retry2.status_code == 200
    assert retry2.json()["status"] == "RETRY_INITIATED"

    # Simulate failure on attempt 3
    db_payment.status = "FAILED"
    db_order.status = "PAYMENT_FAILED"
    db.commit()

    # 3. Retry Attempt 3 -> RETRY_NOT_ALLOWED (exceeded max_payment_retries = 2)
    retry3 = client.post(f"/api/payments/orders/{order_id}/retry", headers=headers)
    assert retry3.status_code == 200
    assert retry3.json()["status"] == "RETRY_NOT_ALLOWED"
    assert "Maximum payment retry limit" in retry3.json()["reason"]
