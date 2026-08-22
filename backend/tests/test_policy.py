from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.merchant_policy import MerchantPolicy
from app.policies.decisions import DecisionType
from app.policies.engine import evaluate_merchant_policy
from app.services.merchant_policy_service import get_merchant_policy


@pytest.fixture
def policy_merchant(db: Session) -> Merchant:
    merchant = Merchant(
        name="Policy Merchant",
        business_name="Policy Merchant LLC",
        email="policy@merchant.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@pytest.fixture
def auth_headers(client: TestClient, policy_merchant: Merchant) -> dict:
    client.post(
        "/api/auth/register",
        json={
            "email": "policyadmin@merchant.demo",
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": str(policy_merchant.id),
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "policyadmin@merchant.demo", "password": "Password123!"},

    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_policy_engine_allow():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
        allow_cross_sell=True,
        allow_upsell=True,
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("1500.00"),
        discount_percent=Decimal("5.00"),
    )
    assert decision.decision == DecisionType.ALLOW
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_policy_engine_amount_exceeded():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("6000.00"),
    )
    assert decision.decision == DecisionType.BLOCK
    assert decision.allowed is False
    assert len(decision.violations) > 0


def test_policy_engine_discount_exceeded():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("1000.00"),
        discount_percent=Decimal("15.00"),
    )
    assert decision.decision == DecisionType.BLOCK
    assert decision.allowed is False
    assert "Discount percentage" in decision.violations[0]


def test_policy_engine_approval_threshold():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("3500.00"),
    )
    assert decision.decision == DecisionType.ALLOW_WITH_APPROVAL
    assert decision.allowed is True
    assert decision.requires_approval is True
    assert len(decision.reasons) > 0


def test_policy_engine_disabled_cross_sell():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
        allow_cross_sell=False,
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("1000.00"),
        has_cross_sell=True,
    )
    assert decision.decision == DecisionType.BLOCK
    assert "Cross-selling is disabled" in decision.violations[0]


def test_policy_engine_disabled_upsell():
    policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
        allow_upsell=False,
    )
    decision = evaluate_merchant_policy(
        policy=policy,
        amount=Decimal("1000.00"),
        has_upsell=True,
    )
    assert decision.decision == DecisionType.BLOCK
    assert "Upselling is disabled" in decision.violations[0]


def test_get_merchant_policy_api(client: TestClient, auth_headers: dict):
    response = client.get("/api/merchant/policy", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert float(data["max_transaction_amount"]) == 5000.0
    assert float(data["approval_threshold"]) == 3000.0


def test_update_merchant_policy_api(client: TestClient, auth_headers: dict):
    update_payload = {
        "max_transaction_amount": 8000.0,
        "approval_threshold": 4000.0,
        "max_discount_percent": 15.0,
    }
    response = client.put(
        "/api/merchant/policy",
        json=update_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["max_transaction_amount"]) == 8000.0
    assert float(data["approval_threshold"]) == 4000.0
    assert float(data["max_discount_percent"]) == 15.0


def test_invalid_policy_values(client: TestClient, auth_headers: dict):
    # threshold > max_transaction_amount
    resp = client.put(
        "/api/merchant/policy",
        json={"max_transaction_amount": 2000.0, "approval_threshold": 3000.0},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


def test_pure_evaluate_policy_with_context():
    from app.policies.context import TransactionContext
    from app.policies.engine import evaluate_policy

    m_policy = MerchantPolicy(
        max_transaction_amount=Decimal("5000.00"),
        max_discount_percent=Decimal("10.00"),
        approval_threshold=Decimal("3000.00"),
    )
    context = TransactionContext(
        amount=Decimal("3500.00"),
        discount_percent=Decimal("5.00"),
    )
    decision = evaluate_policy(merchant_policy=m_policy, buyer_policy=None, context=context)
    assert decision.decision == DecisionType.ALLOW_WITH_APPROVAL
    assert decision.allowed is True
    assert decision.requires_approval is True


