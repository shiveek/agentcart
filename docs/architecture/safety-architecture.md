# AgentCart Safety & Policy Engine Architecture

The **Policy Engine** is a pure, deterministic domain component that evaluates transaction limits, discount thresholds, approval requirements, and buyer spending caps before any payment order can be created.

---

## 1. Pure Deterministic Domain Component

Input:
- `MerchantPolicy`: `max_transaction_amount`, `max_discount_percent`, `approval_threshold`, `max_payment_retries`, boolean flags.
- `BuyerPolicy`: Merchant-scoped buyer limits (`max_daily_spend`, `max_orders_per_day`).
- `TransactionContext`: `cart_subtotal`, `discount_amount`, `item_count`, `buyer_daily_total`.

Output:
- `PolicyDecision`: Status (`ALLOW`, `ALLOW_WITH_APPROVAL`, `BLOCK`) and human-readable reason.

---

## 2. Priority Policy Evaluation Rules

```
Rule 1: BLOCKED if Merchant Policy is inactive
Rule 2: BLOCKED if Transaction Amount > Merchant max_transaction_amount
Rule 3: BLOCKED if Discount Percent > Merchant max_discount_percent
Rule 4: BLOCKED if Buyer Daily Spend > Buyer max_daily_spend
Rule 5: BLOCKED if Buyer Daily Order Count > Buyer max_orders_per_day
Rule 6: ALLOW_WITH_APPROVAL if Transaction Amount > Merchant approval_threshold
Rule 7: ALLOW_WITH_APPROVAL if Buyer Confirmation is required
Rule 8: ALLOW if all rules pass cleanly
```

---

## 3. Visual Safety Bounds

| Order Amount | Policy Status | Action |
| :--- | :--- | :--- |
| **$<\$3,000$** | `ALLOW` | Instant checkout allowed. Razorpay Order created. |
| **$\$3,000 - \$5,000$** | `ALLOW_WITH_APPROVAL` | Order placed in `AWAITING_APPROVAL`. Merchant review required. |
| **$>\$5,000$** | `BLOCK` | Transaction rejected immediately. Payment order creation forbidden. |
