from decimal import Decimal
from typing import Any, List, Optional, Tuple

from app.policies.context import TransactionContext


def check_transaction_rules(
    merchant_policy: Any,
    buyer_policy: Optional[Any],
    context: TransactionContext,
) -> Tuple[List[str], List[str]]:
    """Evaluate all 8 deterministic transaction rules across merchant and buyer policies.
    
    Returns a tuple of (violations, approval_reasons).
    """
    violations: List[str] = []
    approval_reasons: List[str] = []

    # -------------------------------------------------------------
    # Merchant Policy Rule Checks
    # -------------------------------------------------------------
    if merchant_policy is not None:
        m_max_tx = getattr(merchant_policy, "max_transaction_amount", Decimal("5000.00"))
        m_max_disc = getattr(merchant_policy, "max_discount_percent", Decimal("10.00"))
        m_threshold = getattr(merchant_policy, "approval_threshold", Decimal("3000.00"))
        m_allow_cross = getattr(merchant_policy, "allow_cross_sell", True)
        m_allow_up = getattr(merchant_policy, "allow_upsell", True)
        m_req_confirm = getattr(merchant_policy, "require_buyer_confirmation", True)

        # Rule 1: Amount > merchant max_transaction_amount -> BLOCK
        if context.amount > m_max_tx:
            violations.append(
                f"Transaction amount ({context.amount}) exceeds merchant maximum transaction limit ({m_max_tx})"
            )

        # Rule 3: Discount > merchant max_discount_percent -> BLOCK
        if context.discount_percent > m_max_disc:
            violations.append(
                f"Discount percentage ({context.discount_percent}%) exceeds merchant maximum allowed discount ({m_max_disc}%)"
            )

        # Rule 4: Cross-sell requested while disabled -> BLOCK
        if context.has_cross_sell and not m_allow_cross:
            violations.append("Cross-selling is disabled by merchant policy")

        # Rule 5: Upsell requested while disabled -> BLOCK
        if context.has_upsell and not m_allow_up:
            violations.append("Upselling is disabled by merchant policy")

        # Rule 6: Amount > merchant approval_threshold -> ALLOW_WITH_APPROVAL
        if context.amount > m_threshold:
            approval_reasons.append(
                f"Transaction amount ({context.amount}) exceeds merchant approval threshold ({m_threshold})"
            )

        # Rule 8: Merchant requires buyer confirmation AND confirmation missing -> ALLOW_WITH_APPROVAL
        if m_req_confirm and not context.buyer_confirmation_provided:
            approval_reasons.append("Buyer confirmation required by merchant policy but not provided")

    # -------------------------------------------------------------
    # Buyer Policy Rule Checks
    # -------------------------------------------------------------
    if buyer_policy is not None:
        b_max_tx = getattr(buyer_policy, "max_transaction_amount", Decimal("5000.00"))
        b_daily_limit = getattr(buyer_policy, "daily_spending_limit", Decimal("10000.00"))
        b_confirm_above = getattr(buyer_policy, "require_confirmation_above", Decimal("2000.00"))

        # Rule 2: Amount > buyer max_transaction_amount -> BLOCK
        if context.amount > b_max_tx:
            violations.append(
                f"Transaction amount ({context.amount}) exceeds buyer maximum transaction limit ({b_max_tx})"
            )

        # Rule 2b: Daily limit exceeded -> BLOCK
        if (context.daily_spent + context.amount) > b_daily_limit:
            violations.append(
                f"Transaction amount ({context.amount}) plus daily spent ({context.daily_spent}) exceeds buyer daily spending limit ({b_daily_limit})"
            )

        # Rule 7: Amount > buyer require_confirmation_above AND confirmation missing -> ALLOW_WITH_APPROVAL
        if context.amount > b_confirm_above and not context.buyer_confirmation_provided:
            approval_reasons.append(
                f"Transaction amount ({context.amount}) exceeds buyer confirmation threshold ({b_confirm_above}) and confirmation was not provided"
            )

    return violations, approval_reasons
