# AgentCart 5-Minute Pitch & Demo Guide

Follow this step-by-step 5-minute flow for hackathon judging and live demonstrations.

---

## Demo Schedule (5 Minutes Total)

### 0:00 – 0:30 | Problem & Value Proposition
- Introduce AgentCart: AI-native commerce infrastructure designed to let merchants safely monetize autonomous AI buyers.
- Explain the key innovation: Server-side Policy Engine governance + Razorpay payment security.

### 0:30 – 1:40 | AI Product Discovery (`/buyer`)
- Open the AI Buyer Shopping interface at `/buyer`.
- Enter prompt: *"I need a programming keyboard under ₹3000."*
- Show AI Agent response: Recommends **Mechanical Keyboard** at **₹2,499.00** with execution trace ("Catalog searched", "Product matched").
- Click **[Add to Cart]**.

### 1:40 – 2:10 | Automated Cross-Sell Recommendation
- Enter prompt: *"Add a mouse."*
- Show AI Agent response: Detects cross-sell rule and recommends **Wireless Mouse** at **₹699.00**.
- Click **[Add to Cart]**.
- Show Cart Panel: Subtotal **₹3,198.00** computed authoritatively by server DB.

### 2:10 – 2:45 | Policy Engine Evaluation & Approval Controls
- Click **[Policy Checkout]**.
- Policy Engine evaluates transaction (₹3,198.00 is above ₹3,000 threshold $\rightarrow$ `ALLOW_WITH_APPROVAL` or `READY_FOR_PAYMENT`).
- Highlight server safety bounds diagram: $<\$3,000$ ALLOW, $\$3,000-\$5,000$ APPROVAL, $>\$5,000$ BLOCK.

### 2:45 – 3:30 | Razorpay Test Mode Payment & Signature Check
- Launch Razorpay Test Mode Checkout modal using server-created `razorpay_order_id`.
- Complete test payment with simulated test credentials.
- Show backend HMAC-SHA256 signature verification (`POST /api/payments/verify`) marking internal Order as **PAID**.

### 3:30 – 4:10 | Merchant Governance Dashboard & Audit Stream (`/merchant/dashboard`)
- Navigate to `/merchant/dashboard`.
- Show live metrics: Total Revenue, AI-Assisted Revenue, Recent Transactions, and Live Audit Stream.

### 4:10 – 4:40 | Blocked Spending Limit Demo
- Demonstrate adding items over ₹5,000 to cart.
- Show Policy Engine blocking checkout with clear error: *"Payment cannot proceed because transaction exceeds AI spending limit of ₹5,000."*
- Confirm Razorpay Order is NOT created.

### 4:40 – 5:00 | Payment Failure Recovery & Wrap-Up
- Show failed payment handling and policy retry flow (`POST /api/payments/orders/{order_id}/retry`).
- Conclude demo.
