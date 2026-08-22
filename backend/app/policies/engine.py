from decimal import Decimal
from typing import Any, Optional

from app.policies.context import TransactionContext
from app.policies.decisions import DecisionType, PolicyDecision
from app.policies.rules import check_transaction_rules


def evaluate_policy(
    merchant_policy: Any,
    buyer_policy: Optional[Any],
    context: TransactionContext,
) -> PolicyDecision:
    """Pure, deterministic domain entry point for Policy Engine evaluation.
    
    Inputs:
        - merchant_policy: Merchant policy configuration
        - buyer_policy: Optional AI buyer spending policy configuration
        - context: Pure TransactionContext domain object
    
    Output:
        - PolicyDecision (ALLOW, ALLOW_WITH_APPROVAL, or BLOCK)
    """
    violations, approval_reasons = check_transaction_rules(
        merchant_policy=merchant_policy,
        buyer_policy=buyer_policy,
        context=context,
    )

    # Order Priority: BLOCK > ALLOW_WITH_APPROVAL > ALLOW
    if violations:
        return PolicyDecision(
            decision=DecisionType.BLOCK,
            allowed=False,
            requires_approval=False,
            reasons=approval_reasons,
            violations=violations,
        )

    if approval_reasons:
        return PolicyDecision(
            decision=DecisionType.ALLOW_WITH_APPROVAL,
            allowed=True,
            requires_approval=True,
            reasons=approval_reasons,
            violations=[],
        )

    return PolicyDecision(
        decision=DecisionType.ALLOW,
        allowed=True,
        requires_approval=False,
        reasons=[],
        violations=[],
    )


def evaluate_merchant_policy(
    policy: Any,
    amount: Decimal,
    discount_percent: Decimal = Decimal("0.00"),
    has_cross_sell: bool = False,
    has_upsell: bool = False,
    buyer_confirmation_provided: bool = True,
) -> PolicyDecision:
    """Convenience helper for evaluating merchant policy directly."""
    context = TransactionContext(
        amount=amount,
        discount_percent=discount_percent,
        has_cross_sell=has_cross_sell,
        has_upsell=has_upsell,
        buyer_confirmation_provided=buyer_confirmation_provided,
    )
    return evaluate_policy(merchant_policy=policy, buyer_policy=None, context=context)


def evaluate_buyer_policy(
    policy: Any,
    amount: Decimal,
    daily_spent: Decimal = Decimal("0.00"),
    buyer_confirmation_provided: bool = False,
) -> PolicyDecision:
    """Convenience helper for evaluating AI buyer policy directly."""
    context = TransactionContext(
        amount=amount,
        daily_spent=daily_spent,
        buyer_confirmation_provided=buyer_confirmation_provided,
    )
    return evaluate_policy(merchant_policy=None, buyer_policy=policy, context=context)



def evaluate_transaction_policies(
    merchant_policy: Any,
    buyer_policy: Optional[Any],
    amount: Decimal,
    discount_percent: Decimal = Decimal("0.00"),
    has_cross_sell: bool = False,
    has_upsell: bool = False,
    buyer_confirmation_provided: bool = True,
    daily_spent: Decimal = Decimal("0.00"),
) -> PolicyDecision:
    """Convenience helper for evaluating combined merchant and buyer policies."""
    context = TransactionContext(
        amount=amount,
        discount_percent=discount_percent,
        has_cross_sell=has_cross_sell,
        has_upsell=has_upsell,
        buyer_confirmation_provided=buyer_confirmation_provided,
        daily_spent=daily_spent,
    )
    return evaluate_policy(
        merchant_policy=merchant_policy,
        buyer_policy=buyer_policy,
        context=context,
    )
