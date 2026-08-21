import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.relationship import (
    ProductRelationshipCreate,
    ProductRelationshipResponse,
)
from app.services import relationship_service

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
    db: Session = Depends(get_db),
) -> ProductRelationshipResponse:
    """Create relationship endpoint."""
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
    product_id: uuid.UUID, db: Session = Depends(get_db)
) -> List[ProductRelationshipResponse]:
    """Get relationships endpoint."""
    rels = relationship_service.get_product_relationships(db, product_id)
    return [ProductRelationshipResponse.model_validate(r) for r in rels]
