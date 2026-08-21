import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter(tags=["Products"])


@router.post(
    "/merchants/{merchant_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product for merchant",
    description="Adds a new product to a merchant's inventory catalog.",
)
def create_product(
    merchant_id: uuid.UUID,
    product_in: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Create product endpoint."""
    product = product_service.create_product(db, merchant_id, product_in)
    return ProductResponse.model_validate(product)


@router.get(
    "/merchants/{merchant_id}/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List merchant products",
    description="Retrieves a paginated list of products for a given merchant with search and price filters.",
)
def list_products(
    merchant_id: uuid.UUID,
    search: Optional[str] = Query(None, description="Search term across name, description, and SKU"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    """List products endpoint."""
    items, total, total_pages = product_service.list_products(
        db,
        merchant_id=merchant_id,
        search=search,
        category=category,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
    )
    product_responses = [ProductResponse.model_validate(p) for p in items]
    return ProductListResponse(
        items=product_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product details",
    description="Retrieves details for a single product by ID.",
)
def get_product(
    product_id: uuid.UUID, db: Session = Depends(get_db)
) -> ProductResponse:
    """Get product endpoint."""
    product = product_service.get_product(db, product_id)
    return ProductResponse.model_validate(product)


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product details",
    description="Updates existing product attributes.",
)
def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Update product endpoint."""
    product = product_service.update_product(db, product_id, product_in)
    return ProductResponse.model_validate(product)


@router.delete(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate product",
    description="Deactivates a product from active catalog listings.",
)
def delete_product(
    product_id: uuid.UUID, db: Session = Depends(get_db)
) -> ProductResponse:
    """Delete/Deactivate product endpoint."""
    product = product_service.delete_product(db, product_id)
    return ProductResponse.model_validate(product)
