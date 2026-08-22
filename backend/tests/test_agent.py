import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agent.tools.cart_tools import (
    add_item_to_cart_tool,
    create_cart_tool,
    get_cart_summary_tool,
)
from app.agent.tools.catalog_tools import (
    get_product_details_tool,
    search_catalog_tool,
)
from app.agent.tools.order_tools import checkout_cart_tool
from app.models.merchant import Merchant
from app.schemas.product import ProductCreate
from app.services import merchant_policy_service, product_service


def _setup_test_merchant_and_product(db: Session):
    """Helper to create a merchant and sample product in test DB."""
    merchant = Merchant(
        name="Agentic Electronics",
        business_name="Agentic Electronics Ltd",
        email=f"agent_{uuid.uuid4().hex[:6]}@store.demo",
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    product_in = ProductCreate(
        sku=f"AG-KB-{uuid.uuid4().hex[:4]}",
        name="Agent Pro Keyboard",
        description="Autonomous mechanical keyboard",
        category="Keyboards",
        price=Decimal("2999.00"),
        currency="INR",
        initial_quantity=50,
        reorder_level=5,
    )
    product = product_service.create_product(db, merchant.id, product_in)

    merchant_policy_service.get_merchant_policy(db, merchant.id)
    return merchant, product


def test_catalog_and_cart_tools(db: Session):
    merchant, product = _setup_test_merchant_and_product(db)

    # 1. Search Catalog Tool
    search_res = search_catalog_tool(
        merchant_id=str(merchant.id),
        db=db,
        query="Keyboard",
    )
    assert search_res["total_count"] == 1
    assert search_res["products"][0]["sku"] == product.sku

    # 2. Product Details Tool
    details = get_product_details_tool(str(product.id), db)
    assert details["name"] == "Agent Pro Keyboard"
    assert details["in_stock"] is True

    # 3. Create Cart Tool
    cart_res = create_cart_tool(str(merchant.id), "test-agent-buyer", db)
    cart_id = cart_res["cart_id"]
    assert cart_res["status"] == "ACTIVE"

    # 4. Add Item to Cart Tool
    add_res = add_item_to_cart_tool(str(merchant.id), cart_id, str(product.id), 1, db)
    assert add_res["quantity"] == 1
    assert float(add_res["cart_total"]) == 2999.00

    # 5. Cart Summary Tool
    summary = get_cart_summary_tool(str(merchant.id), cart_id, db)
    assert float(summary["total"]) == 2999.00

    # 6. Checkout Cart Tool
    chk_res = checkout_cart_tool(str(merchant.id), cart_id, db)
    assert chk_res["status"] in ["APPROVED", "AWAITING_APPROVAL"]
    assert chk_res["policy_status"] in ["ALLOWED", "APPROVAL_REQUIRED"]


def test_agent_chat_api(client: TestClient, db: Session):
    merchant, product = _setup_test_merchant_and_product(db)

    # Test Search & Add to Cart prompt
    payload = {
        "merchant_id": str(merchant.id),
        "customer_identifier": "agent-demo-user",
        "message": "Search for keyboard and add to cart",
    }
    response = client.post("/api/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["tool_calls"]) >= 2
    cart_id = data["cart_id"]
    assert cart_id is not None

    # Test Checkout prompt with active cart
    chk_payload = {
        "merchant_id": str(merchant.id),
        "customer_identifier": "agent-demo-user",
        "message": "Checkout my cart",
        "cart_id": cart_id,
    }
    chk_response = client.post("/api/agent/chat", json=chk_payload)
    assert chk_response.status_code == 200
    chk_data = chk_response.json()
    assert "Successfully processed checkout" in chk_data["reply"]
    assert chk_data["order_id"] is not None
