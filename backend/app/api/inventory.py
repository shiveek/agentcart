import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.merchant import Merchant
from app.schemas.inventory import InventoryResponse, InventoryUpdate
from app.services import inventory_service, product_service

router = APIRouter(prefix="/products", tags=["Inventory"])


@router.get(
    "/{product_id}/inventory",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product inventory",
    description="Retrieves stock quantity, reserved count, and calculated available stock for a product.",
)
def get_inventory(
    product_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> InventoryResponse:
    """Get inventory endpoint with tenant scoping."""
    product = product_service.get_product(db, product_id)
    if product.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    inventory = inventory_service.get_inventory_by_product_id(db, product_id)
    return InventoryResponse.model_validate(inventory)


@router.put(
    "/{product_id}/inventory",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product inventory",
    description="Updates total stock quantity, reserved reservations, and reorder threshold for a product.",
)
def update_inventory(
    product_id: uuid.UUID,
    inventory_in: InventoryUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> InventoryResponse:
    """Update inventory endpoint with tenant scoping."""
    product = product_service.get_product(db, product_id)
    if product.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    inventory = inventory_service.update_inventory(db, product_id, inventory_in)
    return InventoryResponse.model_validate(inventory)
