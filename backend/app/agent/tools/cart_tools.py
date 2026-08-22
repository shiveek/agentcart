import uuid
from typing import Any, Dict, Union

from sqlalchemy.orm import Session

from app.schemas.cart import CartCreate, CartItemCreate
from app.services import cart_service


def _to_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val))


def create_cart_tool(
    merchant_id: Union[str, uuid.UUID],
    customer_identifier: str,
    db: Session,
    actor_id: str = "AI_AGENT",
) -> Dict[str, Any]:
    """Structured tool for AI Agent to create a new shopping cart."""
    m_uuid = _to_uuid(merchant_id)
    cart_in = CartCreate(customer_identifier=customer_identifier)
    cart = cart_service.create_cart(db, m_uuid, cart_in, actor_id=actor_id)
    return {
        "cart_id": str(cart.id),
        "merchant_id": str(cart.merchant_id),
        "customer_identifier": cart.customer_identifier,
        "status": cart.status,
        "currency": cart.currency,
    }


def add_item_to_cart_tool(
    merchant_id: Union[str, uuid.UUID],
    cart_id: Union[str, uuid.UUID],
    product_id: Union[str, uuid.UUID],
    quantity: int,
    db: Session,
    actor_id: str = "AI_AGENT",
) -> Dict[str, Any]:
    """Structured tool for AI Agent to add a product to a cart.
    
    Prices are securely locked using server-side DB lookups.
    """
    m_uuid = _to_uuid(merchant_id)
    c_uuid = _to_uuid(cart_id)
    p_uuid = _to_uuid(product_id)

    item_in = CartItemCreate(product_id=p_uuid, quantity=quantity)
    item = cart_service.add_cart_item(db, m_uuid, c_uuid, item_in, actor_id=actor_id)
    cart = cart_service.get_cart(db, m_uuid, c_uuid)
    summary = cart_service.calculate_cart_totals(cart)

    return {
        "item_id": str(item.id),
        "cart_id": str(item.cart_id),
        "product_id": str(item.product_id),
        "quantity": item.quantity,
        "unit_price": str(item.unit_price),
        "cart_total": str(summary["total"]),
    }


def get_cart_summary_tool(
    merchant_id: Union[str, uuid.UUID],
    cart_id: Union[str, uuid.UUID],
    db: Session,
) -> Dict[str, Any]:
    """Structured tool for AI Agent to view cart item details and financial totals."""
    m_uuid = _to_uuid(merchant_id)
    c_uuid = _to_uuid(cart_id)
    cart = cart_service.get_cart(db, m_uuid, c_uuid)
    return cart_service.calculate_cart_totals(cart)
