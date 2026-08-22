# AgentCart — AI-Native Commerce for Merchants

> **Track 01: AI Growth & Agentic Commerce**  
> *Razorpay AI Builder Internship 2026 Submission*

AgentCart is a production-oriented AI-native commerce infrastructure platform designed to make merchant product catalogs safely transactable by autonomous AI buyers. It combines an autonomous AI Commerce Agent with a deterministic server-side Policy Engine and secure Razorpay Test Mode payment integration.

---

## 🌐 Live Public Deployment Links

- **Live Frontend Application (Vercel)**: [https://agentcart-frontend.vercel.app](https://agentcart-frontend.vercel.app)
- **Live Backend API (Render / Railway)**: [https://agentcart-api.onrender.com](https://agentcart-api.onrender.com)
- **API Health Endpoint**: [https://agentcart-api.onrender.com/health](https://agentcart-api.onrender.com/health)
- **API Swagger Documentation**: [https://agentcart-api.onrender.com/docs](https://agentcart-api.onrender.com/docs)
- **Razorpay Public Webhook Endpoint**: [https://agentcart-api.onrender.com/api/webhooks/razorpay](https://agentcart-api.onrender.com/api/webhooks/razorpay)

---

## 🌟 Pitch & Problem Statement

### The Problem
Traditional e-commerce platforms were designed for human shoppers using visual browsers. As autonomous AI agents evolve into shopping delegates, merchants lack the infrastructure to safely authorize, govern, and monetize AI-driven purchases without exposing themselves to pricing tampering, spending limit breaches, or unverified payment callbacks.

### The Solution: AgentCart
AgentCart empowers merchants to publish AI-readable product catalogs, expose automated cross-sell opportunities, and enforce strict, server-side Policy Engine governance (`ALLOW`, `ALLOW_WITH_APPROVAL`, `BLOCK`) before delegating payments to Razorpay.

---

## 🚀 Key Features

1. **AI Commerce Agent & Structured Tools**: Autonomous conversational product discovery and cross-selling powered by structured tools (`search_catalog`, `get_recommendations`, `add_to_cart`, `checkout_cart`).
2. **Pure Deterministic Policy Engine**: Evaluates transaction amounts, discount percentages, approval thresholds, and buyer spending caps before any payment order can be created.
3. **Razorpay Test Mode Integration**: Server-side Razorpay order creation in integer paise, constant-time HMAC-SHA256 signature verification, and idempotent webhook replay protection.
4. **Merchant Governance Suite**: Full React dashboard with real KPI metrics, product catalog management, cross-sell opportunity center, policy configuration, transaction inspect drawers, and live audit streams.
5. **Money & Secret Safety**: Secret isolation (`RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` are strictly server-side), zero client-side pricing authority, and complete audit trail.

---

## 🏗️ System Architecture

```
[ AI Buyer / Client UI (Vercel) ]
                 │
                 │ 1. Conversational Intent & Tool Execution (HTTPS)
                 ▼
┌────────────────────────────────────────────────────────┐
│             FastAPI Backend (Render / Railway)          │
├──────────────────────────┬─────────────────────────────┤
│ Commerce Agent           │  Structured Tool Suite      │
│ (Catalog & Cross-Sell)   │  (Catalog, Cart, Orders)    │
└────────────┬─────────────┴──────────────┬──────────────┘
             │                            │
             │ 2. Tool Execution          │ 3. State Mutation
             ▼                            ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│ Pure Policy Engine       │   │ Managed PostgreSQL       │
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

> **The Golden Rule**: *"The LLM proposes actions; deterministic backend services authorize and execute them."*

---

## 🛡️ Policy Engine Safety Bounds

| Order Amount | Policy Status | Action |
| :--- | :--- | :--- |
| **$<\$3,000$** | `ALLOW` | Instant checkout allowed. Razorpay Order created. |
| **$\$3,000 - \$5,000$** | `ALLOW_WITH_APPROVAL` | Order placed in `AWAITING_APPROVAL`. Merchant review required. |
| **$>\$5,000$** | `BLOCK` | Transaction rejected immediately. Payment order creation forbidden. |

---

## 💻 Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Pydantic v2, PyJWT, Argon2 (`pwdlib`).
- **Payments**: Razorpay Python SDK (`razorpay`), HMAC-SHA256 Webhook & Payment Callback verification.
- **Frontend**: React 18, Vite 6, Tailwind CSS v4, Lucide React, Axios, React Router DOM v6.
- **Deployment**: Vercel (Frontend SPA), Render / Railway (Backend API), Managed PostgreSQL.

---

## 📁 Repository Structure

```
agentcart/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── agent/            # AI Agent service & structured tool suite
│   │   ├── api/              # FastAPI routers (auth, merchants, products, carts, orders, payments, webhooks)
│   │   ├── core/             # App settings, logging, security, exception handling
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── policies/         # Pure deterministic Policy Engine
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic services
│   ├── tests/                # Automated pytest suite (58 test cases)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                  # React UI components & context providers
│   ├── vercel.json           # Vercel SPA route rewrite rules
│   └── package.json
├── docs/                     # Architecture, Pitch & Demo documentation
├── render.yaml               # 1-Click Render deployment configuration
└── scripts/
    └── seed_data.py          # Demo merchant & product seed script
```

---

## 🛠️ Setup & Running Locally

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python ../scripts/seed_data.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend App URL: `http://127.0.0.1:5173`

---

## 🔑 Demo Credentials

- **Merchant Admin Login**: `admin@technest.demo`
- **Password**: `Password123!`
- **Demo Buyer ID**: `demo-buyer-001`

---

## 🧪 Testing

Run complete backend test suite:
```bash
cd backend
pytest -q
```
*Expected: 58 passed in ~2.4s*

Run frontend production build test:
```bash
cd frontend
npm run build
```
*Expected: Build succeeded with 0 errors*

---

## 📜 Documentation References
- [System Architecture](docs/architecture/system-architecture.md)
- [AI Agent Architecture](docs/architecture/agent-architecture.md)
- [Safety & Policy Architecture](docs/architecture/safety-architecture.md)
- [Razorpay Payment Lifecycle Flow](docs/architecture/payment-flow.md)
- [5-Minute Pitch Script](docs/demo/pitch-script.md)
- [Demo Flow Guide](docs/demo/demo-flow.md)

---

## ⚖️ License
Built for the **Razorpay AI Builder Internship 2026** (Track 01 — AI Growth & Agentic Commerce).
