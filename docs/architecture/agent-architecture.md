# AgentCart AI Agent Architecture

AgentCart's AI Agent enables conversational product discovery, intelligent cross-selling, and automated cart management without granting the LLM direct access to database state or payment credentials.

---

## The Golden Rule of Agentic Commerce

> **"The LLM proposes actions; deterministic backend services authorize and execute them."**

```
USER PROMPT ("I need a keyboard under ₹3000")
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│                   AI Commerce Agent                      │
├──────────────────────────────────────────────────────────┤
│ - Parses buyer intent & constraints                      │
│ - Selects structured tools (search_catalog, add_to_cart) │
│ - Formulates conversational recommendation response       │
└──────────────────────────┬───────────────────────────────┘
                           │
                           │ Executes Structured Tool
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   Structured Tools                       │
├──────────────────────────────────────────────────────────┤
│ catalog_tools.py      │ search_catalog_tool()           │
│ recommendation_tools  │ get_recommendations_tool()      │
│ cart_tools.py         │ add_item_to_cart_tool()         │
│ order_tools.py        │ checkout_cart_tool()            │
└──────────────────────────┬───────────────────────────────┘
                           │
                           │ Strictly Validates Prices & Inventory
                           ▼
┌──────────────────────────────────────────────────────────┐
│               Database & Business Services               │
│ (Prices snapshot server-side, stock verified in DB)      │
└──────────────────────────────────────────────────────────┘
```

---

## Agentic Tools Inventory

1. `search_catalog_tool`: Browses merchant catalog with category, price range, and stock filters.
2. `get_product_details_tool`: Inspects SKU specifications and real-time inventory quantity.
3. `get_recommendations_tool`: Queries merchant cross-sell and frequently-bought-together graph rules.
4. `create_cart_tool` & `add_item_to_cart_tool`: Creates cart and locks prices using DB lookups.
5. `checkout_cart_tool`: Triggers Policy Engine evaluation and order creation.
