import uuid
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.services import order_service


def _to_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val))


def checkout_cart_tool(
    merchant_id: Union[str, uuid.UUID],
    cart_id: Union[str, uuid.UUID],
    db: Session,
    actor_id: str = "AI_AGENT",
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured tool for AI Agent to checkout a cart and create an Order.
    
    Triggers inventory revalidation, product snapshotting, pure Policy Engine evaluation, and audit logging.
    """
    m_uuid = _to_uuid(merchant_id)
    c_uuid = _to_uuid(cart_id)
    res = order_service.create_order_from_cart(
        db, merchant_id=m_uuid, cart_id=c_uuid, actor_id=actor_id, idempotency_key=idempotency_key
    )
    order = res[0] if isinstance(res, tuple) else res

    return {
        "order_id": str(order.id),
        "merchant_id": str(order.merchant_id),
        "customer_identifier": order.customer_identifier,
        "status": order.status,
        "policy_status": order.policy_status,
        "approval_status": order.approval_status,
        "total": str(order.total),
        "currency": order.currency,
        "items_count": len(order.items),
    }


def get_order_status_tool(
    merchant_id: Union[str, uuid.UUID],
    order_id: Union[str, uuid.UUID],
    db: Session,
) -> Dict[str, Any]:
    """Structured tool for AI Agent to inspect order status and policy governance outcomes."""
    m_uuid = _to_uuid(merchant_id)
    o_uuid = _to_uuid(order_id)
    order = order_service.get_order(db, merchant_id=m_uuid, order_id=o_uuid)

    return {
        "order_id": str(order.id),
        "status": order.status,
        "policy_status": order.policy_status,
        "approval_status": order.approval_status,
        "total": str(order.total),
        "currency": order.currency,
        "created_at": order.created_at.isoformat(),
    }
