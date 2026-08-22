import uuid
from decimal import Decimal

from app.models.buyer_policy import BuyerPolicy
from app.policies.decisions import DecisionType
from app.policies.engine import evaluate_buyer_policy


def test_buyer_policy_allow():
    policy = BuyerPolicy(
        merchant_id=uuid.uuid4(),
        customer_identifier="test-buyer-001",
        max_transaction_amount=Decimal("5000.00"),
        daily_spending_limit=Decimal("10000.00"),
        require_confirmation_above=Decimal("2000.00"),
    )
    decision = evaluate_buyer_policy(
        policy=policy,
        amount=Decimal("1500.00"),
        daily_spent=Decimal("1000.00"),
    )
    assert decision.decision == DecisionType.ALLOW
    assert decision.allowed is True


def test_buyer_policy_limit_exceeded():
    policy = BuyerPolicy(
        merchant_id=uuid.uuid4(),
        customer_identifier="test-buyer-002",
        max_transaction_amount=Decimal("5000.00"),
        daily_spending_limit=Decimal("10000.00"),
        require_confirmation_above=Decimal("2000.00"),
    )
    decision = evaluate_buyer_policy(
        policy=policy,
        amount=Decimal("6000.00"),
    )
    assert decision.decision == DecisionType.BLOCK
    assert "exceeds buyer maximum transaction limit" in decision.violations[0]


def test_buyer_policy_daily_limit_exceeded():
    policy = BuyerPolicy(
        merchant_id=uuid.uuid4(),
        customer_identifier="test-buyer-003",
        max_transaction_amount=Decimal("5000.00"),
        daily_spending_limit=Decimal("10000.00"),
        require_confirmation_above=Decimal("2000.00"),
    )
    decision = evaluate_buyer_policy(
        policy=policy,
        amount=Decimal("4000.00"),
        daily_spent=Decimal("7000.00"),
    )
    assert decision.decision == DecisionType.BLOCK
    assert "exceeds buyer daily spending limit" in decision.violations[0]


def test_buyer_policy_confirmation_threshold():
    policy = BuyerPolicy(
        merchant_id=uuid.uuid4(),
        customer_identifier="test-buyer-004",
        max_transaction_amount=Decimal("5000.00"),
        daily_spending_limit=Decimal("10000.00"),
        require_confirmation_above=Decimal("2000.00"),
    )
    decision = evaluate_buyer_policy(
        policy=policy,
        amount=Decimal("2500.00"),
    )
    assert decision.decision == DecisionType.ALLOW_WITH_APPROVAL
    assert decision.requires_approval is True
