from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.merchant import Merchant
from app.models.product import Product


@pytest.fixture
def cart_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Cart Merchant",
        business_name="Cart Merchant LLC",
        email="cart@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@pytest.fixture
def other_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Other Merchant",
        business_name="Other Merchant LLC",
        email="other@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@pytest.fixture
def auth_headers(client: TestClient, cart_merchant: Merchant) -> dict:
    client.post(
        "/api/auth/register",
        json={
            "email": "cartadmin@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(cart_merchant.id),
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "cartadmin@merchant.demo", "password": "Password123!"},

    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cart_product(db: Session, cart_merchant: Merchant) -> Product:
    product = Product(
        merchant_id=cart_merchant.id,
        sku="TEST-KB-01",
        name="Test Mechanical Keyboard",
        description="RGB Mechanical Keyboard",
        category="Keyboards",
        price=Decimal("1500.00"),
        is_active=True,
    )
    db.add(product)
    db.flush()

    inv = Inventory(
        product_id=product.id,
        quantity=10,
        reserved_quantity=0,
    )
    db.add(inv)
    db.commit()
    db.refresh(product)
    return product


def test_create_cart(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-101", "currency": "INR"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_identifier"] == "buyer-test-101"
    assert data["status"] == "ACTIVE"
    assert data["items"] == []


def test_add_product_to_cart(client: TestClient, auth_headers: dict, cart_product: Product):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-102"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    add_resp = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(cart_product.id), "quantity": 2},
        headers=auth_headers,
    )
    assert add_resp.status_code == 201
    item_data = add_resp.json()
    assert item_data["quantity"] == 2
    assert float(item_data["unit_price"]) == 1500.0


def test_add_insufficient_inventory(client: TestClient, auth_headers: dict, cart_product: Product):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-103"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    add_resp = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(cart_product.id), "quantity": 50},  # stock is 10
        headers=auth_headers,
    )
    assert add_resp.status_code == 400
    assert "Insufficient stock" in add_resp.json()["detail"]


def test_add_inactive_product(client: TestClient, db: Session, auth_headers: dict, cart_merchant: Merchant):
    p_inactive = Product(
        merchant_id=cart_merchant.id,
        sku="INACTIVE-01",
        name="Inactive Item",
        description="Desc",
        category="Test",
        price=Decimal("100.00"),
        is_active=False,
    )
    db.add(p_inactive)
    db.commit()

    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-104"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    add_resp = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(p_inactive.id), "quantity": 1},
        headers=auth_headers,
    )
    assert add_resp.status_code == 400
    assert "inactive" in add_resp.json()["detail"]


def test_add_other_merchant_product(client: TestClient, db: Session, auth_headers: dict, other_merchant: Merchant):
    p_other = Product(
        merchant_id=other_merchant.id,
        sku="OTHER-01",
        name="Other Item",
        description="Desc",
        category="Test",
        price=Decimal("100.00"),
        is_active=True,
    )
    db.add(p_other)
    db.commit()

    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-105"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    add_resp = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(p_other.id), "quantity": 1},
        headers=auth_headers,
    )
    assert add_resp.status_code == 404


def test_update_and_remove_cart_item(client: TestClient, auth_headers: dict, cart_product: Product):
    cart_resp = client.post(
        "/api/carts",
        json={"customer_identifier": "buyer-test-106"},
        headers=auth_headers,
    )
    cart_id = cart_resp.json()["id"]

    add_resp = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": str(cart_product.id), "quantity": 1},
        headers=auth_headers,
    )
    item_id = add_resp.json()["id"]

    # Update quantity
    update_resp = client.put(
        f"/api/carts/{cart_id}/items/{item_id}",
        json={"quantity": 3},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["quantity"] == 3

    # Check Summary
    summary_resp = client.get(f"/api/carts/{cart_id}/summary", headers=auth_headers)
    assert summary_resp.status_code == 200
    assert float(summary_resp.json()["total"]) == 4500.0  # 3 * 1500

    # Delete item
    del_resp = client.delete(f"/api/carts/{cart_id}/items/{item_id}", headers=auth_headers)
    assert del_resp.status_code == 240 or del_resp.status_code == 204
