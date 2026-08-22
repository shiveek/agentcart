import uuid
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.services import catalog_service, product_service


def _to_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val))


def search_catalog_tool(
    merchant_id: Union[str, uuid.UUID],
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    limit: int = 10,
) -> Dict[str, Any]:
    """Structured tool for AI Agent to search and browse merchant catalog.
    
    Returns structured product listings including availability and cross-sell rules.
    """
    m_uuid = _to_uuid(merchant_id)
    min_p = Decimal(str(min_price)) if min_price is not None else None
    max_p = Decimal(str(max_price)) if max_price is not None else None

    response = catalog_service.search_ai_catalog(
        db=db,
        merchant_id=m_uuid,
        q=query,
        category=category,
        min_price=min_p,
        max_price=max_p,
        in_stock=in_stock_only if in_stock_only else None,
        limit=limit,
    )
    return response.model_dump()


def get_product_details_tool(
    product_id: Union[str, uuid.UUID], db: Session
) -> Dict[str, Any]:
    """Structured tool for AI Agent to get single product specifications and inventory status."""
    p_uuid = _to_uuid(product_id)
    product = product_service.get_product(db, p_uuid)

    return {
        "id": str(product.id),
        "merchant_id": str(product.merchant_id),
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": str(product.price),
        "currency": product.currency,
        "is_active": product.is_active,
        "available_quantity": product.inventory.available_quantity if product.inventory else 0,
        "in_stock": (product.inventory.available_quantity > 0) if product.inventory else False,
    }
