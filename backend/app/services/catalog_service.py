import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.relationship import ProductRelationship
from app.schemas.catalog import (
    AICatalogAvailability,
    AICatalogCommerceAttributes,
    AICatalogMerchantSummary,
    AICatalogProductItem,
    AICatalogRelatedProduct,
    AICatalogResponse,
)
from app.services.merchant_service import get_merchant


def _build_ai_product_item(product: Product) -> AICatalogProductItem:
    """Helper to convert a Product ORM instance into an AI-readable schema."""
    inv = product.inventory
    available_qty = inv.available_quantity if inv else 0
    in_stock = available_qty > 0

    related_items: List[AICatalogRelatedProduct] = []
    if product.source_relationships:
        for rel in product.source_relationships:
            if rel.is_active and rel.target_product and rel.target_product.is_active:
                target = rel.target_product
                related_items.append(
                    AICatalogRelatedProduct(
                        target_product_id=target.id,
                        sku=target.sku,
                        name=target.name,
                        price=target.price,
                        relationship_type=rel.relationship_type,
                        score=rel.score,
                        reason=rel.reason,
                    )
                )

    return AICatalogProductItem(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        currency=product.currency,
        availability=AICatalogAvailability(
            in_stock=in_stock,
            available_quantity=available_qty,
        ),
        commerce_attributes=AICatalogCommerceAttributes(
            can_recommend=True,
            can_cross_sell=bool(related_items),
        ),
        related_products=related_items,
    )


def get_ai_catalog(db: Session, merchant_id: uuid.UUID) -> AICatalogResponse:
    """Retrieve full AI-readable merchant product catalog."""
    merchant = get_merchant(db, merchant_id)

    products = (
        db.execute(
            select(Product)
            .options(
                selectinload(Product.inventory),
                selectinload(Product.source_relationships).selectinload(
                    ProductRelationship.target_product
                ),
            )
            .where(Product.merchant_id == merchant_id, Product.is_active == True)
            .order_by(Product.name.asc())
        )
        .scalars()
        .all()
    )

    items = [_build_ai_product_item(p) for p in products]

    return AICatalogResponse(
        merchant=AICatalogMerchantSummary(
            id=merchant.id,
            name=merchant.name,
            currency=merchant.currency,
        ),
        products=items,
        total_count=len(items),
    )


def search_ai_catalog(
    db: Session,
    merchant_id: uuid.UUID,
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock: Optional[bool] = None,
    limit: int = 20,
) -> AICatalogResponse:
    """Deterministic DB-backed product search for AI buyer tools."""
    merchant = get_merchant(db, merchant_id)

    query = (
        select(Product)
        .options(
            selectinload(Product.inventory),
            selectinload(Product.source_relationships).selectinload(
                ProductRelationship.target_product
            ),
        )
        .where(Product.merchant_id == merchant_id, Product.is_active == True)
    )

    if q:
        search_pattern = f"%{q}%"
        query = query.where(
            (Product.name.ilike(search_pattern))
            | (Product.description.ilike(search_pattern))
            | (Product.category.ilike(search_pattern))
            | (Product.sku.ilike(search_pattern))
        )
    if category:
        query = query.where(Product.category.ilike(category))
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    products = db.execute(query).scalars().all()

    items = []
    limit = max(1, min(100, limit))

    for p in products:
        item = _build_ai_product_item(p)
        if in_stock is not None:
            if in_stock and not item.availability.in_stock:
                continue
            if not in_stock and item.availability.in_stock:
                continue
        items.append(item)
        if len(items) >= limit:
            break

    return AICatalogResponse(
        merchant=AICatalogMerchantSummary(
            id=merchant.id,
            name=merchant.name,
            currency=merchant.currency,
        ),
        products=items,
        total_count=len(items),
    )
