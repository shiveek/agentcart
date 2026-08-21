import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.catalog import AICatalogResponse
from app.services import catalog_service

router = APIRouter(prefix="/agent/catalog", tags=["AI Agent Catalog"])


@router.get(
    "/{merchant_id}",
    response_model=AICatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI-readable catalog",
    description="Returns structured merchant commerce catalog payload optimized for AI buyer agent consumption.",
)
def get_ai_catalog(
    merchant_id: uuid.UUID, db: Session = Depends(get_db)
) -> AICatalogResponse:
    """Get AI catalog endpoint."""
    return catalog_service.get_ai_catalog(db, merchant_id)


@router.get(
    "/{merchant_id}/search",
    response_model=AICatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Deterministic AI product search",
    description="Deterministic database-backed product query endpoint for AI agent search tools.",
)
def search_ai_catalog(
    merchant_id: uuid.UUID,
    q: Optional[str] = Query(None, description="Search query string"),
    category: Optional[str] = Query(None, description="Product category filter"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter items in stock"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
) -> AICatalogResponse:
    """Search AI catalog endpoint."""
    return catalog_service.search_ai_catalog(
        db,
        merchant_id=merchant_id,
        q=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        limit=limit,
    )
