from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.merchant import Merchant
from app.models.merchant_policy import MerchantPolicy
from app.models.product import Product


@pytest.fixture
def order_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Order Merchant",
        business_name="Order Merchant LLC",
        email="order@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    # Add custom policy
    policy = MerchantPolicy(
        merchant_id=merchant.id,
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("2000.00"),
    )
    db.add(policy)
    db.commit()
    return merchant


@pytest.fixture
def auth_headers(client: TestClient, order_merchant: Merchant) -> dict:
    client.post(
        "/api/auth/register",
        json={
            "email": "orderadmin@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(order_merchant.id),
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "orderadmin@merchant.demo", "password": "Password123!"},

    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def order_products(db: Session, order_merchant: Merchant) -> dict:
    p1 = Product(
        merchant_id=order_merchant.id,
        sku="ITEM-01",
        name="Item Standard",
        description="Standard Item",
        category="Tech",
        price=Decimal("1000.00"),
        is_active=True,
    )
    p2 = Product(
        merchant_id=order_merchant.id,
        sku="ITEM-02",
        name="Item Expensive",
        description="Expensive Item",
        category="Tech",
        price=Decimal("6000.00"),
        is_active=True,
    )
    db.add_all([p1, p2])
    db.flush()

    i1 = Inventory(product_id=p1.id, quantity=20, reserved_quantity=0)
    i2 = Inventory(product_id=p2.id, quantity=5, reserved_quantity=0)
    db.add_all([i1, i2])
    db.commit()
    return {"p1": p1, "p2": p2}


def test_create_order_approved(client: TestClient, auth_headers: dict, order_products: dict):
    # 1. Create Cart
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-ord-1"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    # 2. Add Item 1 (Total = 1000 <= threshold 2000)
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(order_products["p1"].id), "quantity": 1},
        headers=auth_headers,
    )

    # 3. Create Order
    order_resp = client.post(
        f"/api/orders/from-cart/{cart_id}",
        headers=auth_headers,
    )
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["status"] == "APPROVED"
    assert data["policy_status"] == "ALLOWED"
    assert data["approval_status"] == "NOT_REQUIRED"
    assert float(data["total"]) == 1000.0
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name_snapshot"] == "Item Standard"


def test_create_order_awaiting_approval(client: TestClient, auth_headers: dict, order_products: dict):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-ord-2"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    # Total = 3000 > threshold 2000 and <= max 5000
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(order_products["p1"].id), "quantity": 3},
        headers=auth_headers,
    )

    order_resp = client.post(
        f"/api/orders/from-cart/{cart_id}",
        headers=auth_headers,
    )
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["status"] == "AWAITING_APPROVAL"
    assert data["policy_status"] == "APPROVAL_REQUIRED"
    assert data["approval_status"] == "PENDING"


def test_create_order_blocked(client: TestClient, auth_headers: dict, order_products: dict):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-ord-3"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    # Total = 6000 > max_transaction_amount 5000
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(order_products["p2"].id), "quantity": 1},
        headers=auth_headers,
    )

    order_resp = client.post(
        f"/api/orders/from-cart/{cart_id}",
        headers=auth_headers,
    )
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["status"] == "CANCELLED"
    assert data["policy_status"] == "BLOCKED"
    assert "violations" in data and len(data["violations"]) > 0


def test_order_idempotency(client: TestClient, auth_headers: dict, order_products: dict):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-ord-4"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(order_products["p1"].id), "quantity": 1},
        headers=auth_headers,
    )

    idempotency_headers = {
        **auth_headers,
        "Idempotency-Key": "idempotent-key-unique-001",
    }

    r1 = client.post(f"/api/orders/from-cart/{cart_id}", headers=idempotency_headers)
    assert r1.status_code == 201
    o1 = r1.json()

    # Repeat request with same idempotency key
    r2 = client.post(f"/api/orders/from-cart/{cart_id}", headers=idempotency_headers)
    assert r2.status_code == 201
    o2 = r2.json()

    assert o1["id"] == o2["id"]
    assert o1["idempotency_key"] == "idempotent-key-unique-001"
