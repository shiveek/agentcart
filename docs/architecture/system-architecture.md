# AgentCart System Architecture

AgentCart is an **AI-Native Commerce Platform** designed to make merchant product catalogs transactable by autonomous AI buyers while maintaining strict server-side policy governance and Razorpay payment security.

---

## High-Level System Flow

```
[ AI Buyer / Client UI ]
           │
           │ 1. Conversational Intent & Tool Calls
           ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
├──────────────────────────┬─────────────────────────────┤
│ Commerce Agent           │  Structured Tool Suite      │
│ (Catalog & Cross-Sell)   │  (Catalog, Cart, Orders)    │
└────────────┬─────────────┴──────────────┬──────────────┘
             │                            │
             │ 2. Tool Execution          │ 3. State Mutation
             ▼                            ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│ Pure Policy Engine       │   │ SQLAlchemy 2.0 / DB      │
│ (ALLOW/APPROVAL/BLOCK)   │   │ (Merchants, Carts, Orders)│
└────────────┬─────────────┘   └──────────┬───────────────┘
             │                            │
             │ 4. Payment Creation        │
             ▼                            ▼
┌────────────────────────────────────────────────────────┐
│                   Razorpay Gateway                     │
│ (Server-Side Order, HMAC Verification, Webhooks)      │
└────────────────────────────────────────────────────────┘
```

---

## Key Core Modules

1. **Multi-Tenancy & Auth**: JWT Authentication (`pwdlib[argon2]` + PyJWT) with `merchant_admin` and `merchant_staff` roles.
2. **AI-Readable Catalog**: Rich JSON listings containing availability metadata, merchant summary, and cross-sell graph rules.
3. **Pure Policy Engine**: Deterministic 8-rule evaluator determining transaction status (`ALLOW`, `ALLOW_WITH_APPROVAL`, `BLOCK`) without dependencies on FastAPI sessions or LLM code.
4. **Structured Agent Tools**: Server-side tool execution ensuring server-calculated prices, inventory validation, and idempotency.
5. **Razorpay Payment Lifecycle**: Server-side Razorpay order creation in integer paise, constant-time HMAC-SHA256 signature verification, and webhook replay protection.
