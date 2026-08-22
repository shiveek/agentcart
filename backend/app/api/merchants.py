import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.services import merchant_service

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post(
    "",
    response_model=MerchantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create merchant profile",
    description="Registers a new merchant seller profile on AgentCart.",
)
def create_merchant(
    merchant_in: MerchantCreate, db: Session = Depends(get_db)
) -> MerchantResponse:
    """Create merchant endpoint."""
    return merchant_service.create_merchant(db, merchant_in)


@router.get(
    "/{merchant_id}",
    response_model=MerchantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get merchant profile",
    description="Retrieves profile details of the authenticated merchant.",
)
def get_merchant(
    merchant_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantResponse:
    """Get merchant profile endpoint with tenant isolation."""
    if merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Users cannot access another merchant's profile",
        )
    return merchant_service.get_merchant(db, current_merchant.id)


@router.put(
    "/{merchant_id}",
    response_model=MerchantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update merchant profile",
    description="Updates information for an existing merchant profile.",
)
def update_merchant(
    merchant_id: uuid.UUID,
    merchant_in: MerchantUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantResponse:
    """Update merchant profile endpoint with tenant isolation."""
    if merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Users cannot update another merchant's profile",
        )
    return merchant_service.update_merchant(db, current_merchant.id, merchant_in)
