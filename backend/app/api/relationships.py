import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.merchant import Merchant
from app.schemas.relationship import (
    ProductRelationshipCreate,
    ProductRelationshipResponse,
)
from app.services import product_service, relationship_service

router = APIRouter(prefix="/products", tags=["Product Relationships"])


@router.post(
    "/{product_id}/relationships",
    response_model=ProductRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product relationship",
    description="Establishes a cross-sell, upsell, or frequently bought together link between two merchant products.",
)
def create_relationship(
    product_id: uuid.UUID,
    rel_in: ProductRelationshipCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> ProductRelationshipResponse:
    """Create relationship endpoint with tenant scoping."""
    product = product_service.get_product(db, product_id)
    if product.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    rel = relationship_service.create_product_relationship(db, product_id, rel_in)
    return ProductRelationshipResponse.model_validate(rel)


@router.get(
    "/{product_id}/relationships",
    response_model=List[ProductRelationshipResponse],
    status_code=status.HTTP_200_OK,
    summary="Get product relationships",
    description="Retrieves cross-sell and recommendation links where the specified product is the source.",
)
def get_relationships(
    product_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> List[ProductRelationshipResponse]:
    """Get relationships endpoint with tenant scoping."""
    product = product_service.get_product(db, product_id)
    if product.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    rels = relationship_service.get_product_relationships(db, product_id)
    return [ProductRelationshipResponse.model_validate(r) for r in rels]
