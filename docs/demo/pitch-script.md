# AgentCart Pitch Script (Razorpay AI Builder Internship 2026)

---

## 1. Problem
As AI agents evolve from conversational bots into autonomous shopping delegates, merchants face a critical gap: traditional e-commerce platforms were built for humans with web browsers, not AI agents.

Without server-side governance, letting AI buyers purchase items directly risks unauthorized spending, inventory fraud, price manipulation, and unverified payment callbacks.

---

## 2. Solution: AgentCart
AgentCart is an AI-Native Commerce Platform built for merchants. It exposes structured AI-readable catalogs, graph-based cross-sell opportunities, and a deterministic Policy Engine that governs every agent transaction before delegating to Razorpay.

---

## 3. The Core Innovation
1. **The LLM Proposes, The Server Authorizes**: The LLM agent never directly accesses database state or payment keys. It invokes structured tools (`search_catalog`, `add_to_cart`) that enforce server-calculated prices.
2. **Pure Deterministic Policy Engine**: Every checkout request is evaluated against merchant spending caps, discount limits, and approval thresholds.
3. **Razorpay Payment Security**: Razorpay orders are created server-side in integer paise. Client payments are verified using HMAC-SHA256 with database-stored provider order IDs, backed by idempotent webhook replay protection.

---

## 4. Business Impact
Merchants get a turnkey AI storefront that unlocks agentic commerce revenue, automatically drives cross-sell order uplift, and provides complete audit transparency without sacrificing security.
