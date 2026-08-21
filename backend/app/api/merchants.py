import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
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
    description="Retrieves public details of a registered merchant by ID.",
)
def get_merchant(
    merchant_id: uuid.UUID, db: Session = Depends(get_db)
) -> MerchantResponse:
    """Get merchant by ID endpoint."""
    return merchant_service.get_merchant(db, merchant_id)


@router.put(
    "/{merchant_id}",
    response_model=MerchantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update merchant profile",
    description="Updates information for an existing merchant.",
)
def update_merchant(
    merchant_id: uuid.UUID,
    merchant_in: MerchantUpdate,
    db: Session = Depends(get_db),
) -> MerchantResponse:
    """Update merchant endpoint."""
    return merchant_service.update_merchant(db, merchant_id, merchant_in)
