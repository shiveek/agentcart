import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.product import Product
from app.models.relationship import ProductRelationship
from app.schemas.relationship import ProductRelationshipCreate
from app.services.product_service import get_product


def create_product_relationship(
    db: Session, source_product_id: uuid.UUID, rel_in: ProductRelationshipCreate
) -> ProductRelationship:
    """Create a cross-sell/upsell relationship with merchant ownership validation."""
    source_product = get_product(db, source_product_id)

    if source_product_id == rel_in.target_product_id:
        raise BadRequestException(
            message="Source product and target product cannot be the same item."
        )

    target_product = get_product(db, rel_in.target_product_id)

    # Validate both products belong to the same merchant
    if source_product.merchant_id != target_product.merchant_id:
        raise BadRequestException(
            message="Cannot create cross-sell relationship across different merchants."
        )

    # Check for duplicate relationship
    existing = db.execute(
        select(ProductRelationship).where(
            ProductRelationship.source_product_id == source_product_id,
            ProductRelationship.target_product_id == rel_in.target_product_id,
            ProductRelationship.relationship_type == rel_in.relationship_type,
        )
    ).scalar_one_or_none()

    if existing:
        # Update existing score and reason
        existing.score = rel_in.score
        existing.reason = rel_in.reason
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    relationship = ProductRelationship(
        source_product_id=source_product_id,
        target_product_id=rel_in.target_product_id,
        relationship_type=rel_in.relationship_type,
        score=rel_in.score,
        reason=rel_in.reason,
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)
    return relationship


def get_product_relationships(
    db: Session, product_id: uuid.UUID
) -> List[ProductRelationship]:
    """Get active relationships where given product is source."""
    get_product(db, product_id)
    relationships = (
        db.execute(
            select(ProductRelationship)
            .where(
                ProductRelationship.source_product_id == product_id,
                ProductRelationship.is_active == True,
            )
            .order_by(ProductRelationship.score.desc())
        )
        .scalars()
        .all()
    )
    return list(relationships)
