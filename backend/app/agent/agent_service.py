import logging
import uuid
from typing import Any, Dict, List, Optional

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
from app.agent.tools.order_tools import (
    checkout_cart_tool,
    get_order_status_tool,
)
from app.agent.tools.recommendation_tools import get_recommendations_tool
from app.schemas.agent import AgentChatRequest, AgentChatResponse, ToolCallTrace

logger = logging.getLogger("agentcart.agent")


def run_commerce_agent(
    db: Session,
    request: AgentChatRequest,
) -> AgentChatResponse:
    """Executes the AI Commerce Agent workflow for a given natural language directive.
    
    Processes the request through structured agent tools, enforcing commerce rules and Policy Engine checks.
    """
    tool_calls: List[ToolCallTrace] = []
    merchant_id_str = str(request.merchant_id)
    customer_id = request.customer_identifier
    message = request.message.lower()
    cart_id = request.cart_id
    order_id: Optional[uuid.UUID] = None

    # Step 1: Ensure active cart exists if request implies cart/checkout actions
    if not cart_id and any(kw in message for kw in ["cart", "buy", "add", "checkout", "order"]):
        c_res = create_cart_tool(
            merchant_id=merchant_id_str,
            customer_identifier=customer_id,
            db=db,
            actor_id="AI_AGENT",
        )
        cart_id = uuid.UUID(c_res["cart_id"])
        tool_calls.append(
            ToolCallTrace(
                tool_name="create_cart_tool",
                arguments={"merchant_id": merchant_id_str, "customer_identifier": customer_id},
                output=c_res,
            )
        )

    # Step 2: Search catalog if user is looking for products
    search_results = None
    if any(kw in message for kw in ["search", "find", "look", "keyboard", "mouse", "product", "laptop", "webcam"]):
        # Extract search query keyword
        query_term = None
        for word in message.split():
            if word in ["keyboard", "mouse", "stand", "hub", "webcam", "headphones"]:
                query_term = word
                break

        search_results = search_catalog_tool(
            merchant_id=merchant_id_str,
            db=db,
            query=query_term,
            in_stock_only=True,
        )
        tool_calls.append(
            ToolCallTrace(
                tool_name="search_catalog_tool",
                arguments={"merchant_id": merchant_id_str, "query": query_term},
                output={"total_count": search_results["total_count"]},
            )
        )

        # Step 3: Add first matching item to cart if requested
        if cart_id and any(kw in message for kw in ["add", "buy", "put"]):
            products = search_results.get("products", [])
            if products:
                target_prod = products[0]
                add_res = add_item_to_cart_tool(
                    merchant_id=merchant_id_str,
                    cart_id=str(cart_id),
                    product_id=target_prod["id"],
                    quantity=1,
                    db=db,
                    actor_id="AI_AGENT",
                )
                tool_calls.append(
                    ToolCallTrace(
                        tool_name="add_item_to_cart_tool",
                        arguments={"merchant_id": merchant_id_str, "cart_id": str(cart_id), "product_id": target_prod["id"], "quantity": 1},
                        output=add_res,
                    )
                )

                # Fetch cross-sell recommendations
                rec_res = get_recommendations_tool(target_prod["id"], db)
                if rec_res:
                    tool_calls.append(
                        ToolCallTrace(
                            tool_name="get_recommendations_tool",
                            arguments={"product_id": target_prod["id"]},
                            output={"recommendations_count": len(rec_res)},
                        )
                    )

    # Step 4: Checkout cart if requested
    if cart_id and "checkout" in message:
        chk_res = checkout_cart_tool(
            merchant_id=merchant_id_str,
            cart_id=str(cart_id),
            db=db,
            actor_id="AI_AGENT",
            idempotency_key=f"agent-chk-{uuid.uuid4().hex[:8]}",
        )
        order_id = uuid.UUID(chk_res["order_id"])
        tool_calls.append(
            ToolCallTrace(
                tool_name="checkout_cart_tool",
                arguments={"merchant_id": merchant_id_str, "cart_id": str(cart_id)},
                output=chk_res,
            )
        )
        reply = (
            f"Successfully processed checkout! Order #{chk_res['order_id']} is currently "
            f"in status '{chk_res['status']}' with policy decision '{chk_res['policy_status']}'."
        )
    elif cart_id and search_results and search_results.get("products"):
        prod_name = search_results["products"][0]["name"]
        reply = f"Found '{prod_name}' in the catalog and added it to your active cart #{cart_id}."
    elif search_results:
        count = search_results.get("total_count", 0)
        reply = f"Found {count} products matching your request in the catalog."
    else:
        reply = "I am your AI Commerce Assistant. I can help you search the catalog, add items to cart, recommend cross-sells, and execute policy-governed checkouts."

    return AgentChatResponse(
        reply=reply,
        cart_id=cart_id,
        order_id=order_id,
        tool_calls=tool_calls,
        metadata={"merchant_id": merchant_id_str, "customer_identifier": customer_id},
    )
