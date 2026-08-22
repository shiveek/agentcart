import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.merchant import Merchant
from app.models.user import User


@pytest.fixture
def test_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Test Merchant Auth",
        business_name="Test Merchant Auth Inc",
        email="auth@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def test_register_user(client: TestClient, test_merchant: Merchant):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "user1@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(test_merchant.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user1@merchant.demo"
    assert data["role"] == "merchant_admin"
    assert data["merchant_id"] == str(test_merchant.id)
    assert data["is_active"] is True


def test_register_duplicate_email(client: TestClient, test_merchant: Merchant):
    payload = {
        "email": "dup@merchant.demo",
        "password": "Password123!",
        "role": "merchant_staff",
        "merchant_id": str(test_merchant.id),
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]


def test_login_success(client: TestClient, test_merchant: Merchant):
    register_payload = {
        "email": "login@merchant.demo",
        "password": "Password123!",
        "role": "merchant_admin",
        "merchant_id": str(test_merchant.id),
    }
    client.post("/api/auth/register", json=register_payload)

    login_response = client.post(
        "/api/auth/login",
        json={"email": "login@merchant.demo", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, test_merchant: Merchant):
    register_payload = {
        "email": "wrongpwd@merchant.demo",
        "password": "Password123!",
        "role": "merchant_admin",
        "merchant_id": str(test_merchant.id),
    }
    client.post("/api/auth/register", json=register_payload)

    login_response = client.post(
        "/api/auth/login",
        json={"email": "wrongpwd@merchant.demo", "password": "WrongPassword!"},
    )
    assert login_response.status_code == 401
    assert "Incorrect email or password" in login_response.json()["detail"]


def test_get_me(client: TestClient, test_merchant: Merchant):
    client.post(
        "/api/auth/register",
        json={
            "email": "me@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(test_merchant.id),
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "me@merchant.demo", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "me@merchant.demo"
    assert me_data["role"] == "merchant_admin"


def test_inactive_user(client: TestClient, db: Session, test_merchant: Merchant):
    user = User(
        email="inactive@merchant.demo",
        password_hash=hash_password("Password123!"),
        role="merchant_admin",
        merchant_id=test_merchant.id,
        is_active=False,
    )
    db.add(user)
    db.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "inactive@merchant.demo", "password": "Password123!"},
    )
    assert login_resp.status_code == 401
    assert "Inactive" in login_resp.json()["detail"]


def test_tenant_isolation_forbidden(client: TestClient, db: Session, test_merchant: Merchant):
    # Create a second merchant and user
    m2 = Merchant(name="Other Merchant Isolation", business_name="Other Inc", email="otheriso@merchant.demo")
    db.add(m2)
    db.commit()

    client.post(
        "/api/auth/register",
        json={
            "email": "user2iso@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(m2.id),
        },
    )
    token = client.post("/api/auth/login", json={"email": "user2iso@merchant.demo", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access test_merchant's profile using user2iso's token -> 403 Forbidden
    resp = client.get(f"/api/merchants/{test_merchant.id}", headers=headers)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]

