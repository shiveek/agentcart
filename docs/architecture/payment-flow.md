# Payment Architecture & Razorpay Integration Flow

This document details the payment integration architecture in **AgentCart**, focusing on money safety, HMAC-SHA256 signature verification, webhook idempotency, and state transitions.

---

## 1. End-to-End Payment Sequence

```
1. Approved Internal Order
   State: Order.status == "APPROVED"

2. Server-Side Razorpay Order Creation
   Request: POST /api/payments/orders/{order_id}
   Action:
   - Validates internal order state is APPROVED.
   - Calculates exact amount in integer paise (e.g., ₹3,198 -> 319800 paise).
   - Calls Razorpay API server-side to create order.
   - Creates internal Payment record (status: CREATED).
   - Updates internal order status to PAYMENT_PENDING.
   - Returns safe checkout payload: { razorpay_key_id, razorpay_order_id, amount_paise }.

3. Razorpay Checkout (Browser / Client)
   Action:
   - Client opens Razorpay Modal using safe Key ID and server-created Razorpay Order ID.
   - Client executes test mode payment.

4. Server-Side Payment Signature Verification
   Request: POST /api/payments/verify
   Payload: { internal_order_id, razorpay_payment_id, razorpay_order_id, razorpay_signature }
   Security Rule:
   - The server NEVER trusts razorpay_order_id passed from the browser.
   - The server fetches the real provider_order_id from internal Payment DB using internal_order_id.
   - Calculates HMAC-SHA256(provider_order_id + "|" + razorpay_payment_id, RAZORPAY_KEY_SECRET).
   - Performs constant-time comparison via hmac.compare_digest().
   - On success: Payment -> CAPTURED, Order -> PAID.
   - On mismatch: Rejects payment, logs audit PAYMENT_SIGNATURE_REJECTED.

5. Razorpay Webhook Processing
   Request: POST /api/webhooks/razorpay
   Action:
   - Reads raw request body bytes and X-Razorpay-Signature header.
   - Verifies HMAC-SHA256 signature using RAZORPAY_WEBHOOK_SECRET.
   - Enforces replay protection via WebhookEvent table (UNIQUE constraint on provider + provider_event_id).
   - Idempotently updates internal Payment & Order status for payment.captured or payment.failed events.
```

---

## 2. Security & Money Safety Rules

1. **AI Agent Boundaries**: The AI Agent / LLM NEVER calls Razorpay APIs directly. Checkout is executed strictly via backend endpoints after the Policy Engine returns `ALLOW` or `ALLOW_WITH_APPROVAL`.
2. **Secret Isolation**: `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` are strictly server-side variables. They are never returned in API responses, printed in logs, or sent to frontends.
3. **No Client Pricing**: Amount and currency are strictly recalculated server-side from internal approved orders. Client-provided amounts or currencies are ignored.
4. **No Floating Point Money Math**: Monetary values are stored as `Decimal(12, 2)` and converted to integer paise (`int(round(amount * 100))`).
5. **Database-Backed Signature Check**: Razorpay requires server-side payment signature verification before treating a browser-reported payment as genuine. Their integration guide specifies that the order ID used in verification must come from your server/database.
6. **Webhook Idempotency**: Duplicate webhooks are detected via `WebhookEvent` table lookups and return `200 OK` with status `DUPLICATE` without re-executing state changes.
