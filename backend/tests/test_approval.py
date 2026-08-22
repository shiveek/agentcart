from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.merchant import Merchant
from app.models.merchant_policy import MerchantPolicy
from app.models.product import Product


@pytest.fixture
def approval_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Approval Merchant",
        business_name="Approval Merchant Inc",
        email="approval@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    policy = MerchantPolicy(
        merchant_id=merchant.id,
        max_transaction_amount=Decimal("5000.00"),
        approval_threshold=Decimal("1000.00"),
    )
    db.add(policy)
    db.commit()
    return merchant


@pytest.fixture
def auth_headers(client: TestClient, approval_merchant: Merchant) -> dict:
    client.post(
        "/api/auth/register",
        json={
            "email": "approvaladmin@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(approval_merchant.id),
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "approvaladmin@merchant.demo", "password": "Password123!"},

    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def approval_product(db: Session, approval_merchant: Merchant) -> Product:
    product = Product(
        merchant_id=approval_merchant.id,
        sku="APP-ITEM",
        name="Approval Item",
        description="Desc",
        category="Tech",
        price=Decimal("1500.00"),  # > threshold 1000
        is_active=True,
    )
    db.add(product)
    db.flush()
    inv = Inventory(product_id=product.id, quantity=10, reserved_quantity=0)
    db.add(inv)
    db.commit()
    return product


def test_approve_order(client: TestClient, auth_headers: dict, approval_product: Product):
    # 1. Cart & Order requiring approval
    cart_resp = client.post("/api/carts", json={"customer_identifier": "buyer-app-1"}, headers=auth_headers)
    cart_id = cart_resp.json()["id"]

    client.post(f"/api/carts/{cart_id}/items", json={"product_id": str(approval_product.id), "quantity": 1}, headers=auth_headers)
    order_resp = client.post(f"/api/orders/from-cart/{cart_id}", headers=auth_headers)
    order_id = order_resp.json()["id"]
    assert order_resp.json()["status"] == "AWAITING_APPROVAL"

    # 2. Approve
    app_resp = client.post(f"/api/orders/{order_id}/approve", json={"reason": "Approved by manager"}, headers=auth_headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "APPROVED"
    assert app_resp.json()["reason"] == "Approved by manager"

    # Check updated order status
    get_resp = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert get_resp.json()["status"] == "APPROVED"
    assert get_resp.json()["approval_status"] == "APPROVED"


def test_reject_order(client: TestClient, auth_headers: dict, approval_product: Product):
    cart_resp = client.post("/api/carts", json={"customer_identifier": "buyer-app-2"}, headers=auth_headers)
    cart_id = cart_resp.json()["id"]

    client.post(f"/api/carts/{cart_id}/items", json={"product_id": str(approval_product.id), "quantity": 1}, headers=auth_headers)
    order_resp = client.post(f"/api/orders/from-cart/{cart_id}", headers=auth_headers)
    order_id = order_resp.json()["id"]

    # Reject
    rej_resp = client.post(f"/api/orders/{order_id}/reject", json={"reason": "High risk transaction"}, headers=auth_headers)
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"

    get_resp = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert get_resp.json()["status"] == "CANCELLED"
    assert get_resp.json()["approval_status"] == "REJECTED"


def test_cannot_approve_non_pending_order(client: TestClient, auth_headers: dict, approval_product: Product):
    cart_resp = client.post("/api/carts", json={"customer_identifier": "buyer-app-3"}, headers=auth_headers)
    cart_id = cart_resp.json()["id"]

    client.post(f"/api/carts/{cart_id}/items", json={"product_id": str(approval_product.id), "quantity": 1}, headers=auth_headers)
    order_resp = client.post(f"/api/orders/from-cart/{cart_id}", headers=auth_headers)
    order_id = order_resp.json()["id"]

    client.post(f"/api/orders/{order_id}/approve", json={"reason": "Approved once"}, headers=auth_headers)

    # Try approving again
    app2_resp = client.post(f"/api/orders/{order_id}/approve", json={"reason": "Approved twice"}, headers=auth_headers)
    assert app2_resp.status_code == 400
