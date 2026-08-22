import uuid
from typing import Any, Dict, List, Union

from sqlalchemy.orm import Session

from app.services import relationship_service


def _to_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val))


def get_recommendations_tool(
    product_id: Union[str, uuid.UUID], db: Session
) -> List[Dict[str, Any]]:
    """Structured tool for AI Agent to find cross-sell, upsell, and frequently bought together recommendations."""
    p_uuid = _to_uuid(product_id)
    relationships = relationship_service.get_product_relationships(db, p_uuid)

    results = []
    for rel in relationships:
        target = rel.target_product
        results.append({
            "relationship_type": rel.relationship_type,
            "score": str(rel.score),
            "reason": rel.reason,
            "target_product": {
                "id": str(target.id),
                "sku": target.sku,
                "name": target.name,
                "price": str(target.price),
                "category": target.category,
                "in_stock": (target.inventory.available_quantity > 0) if target.inventory else False,
            },
        })
    return results
