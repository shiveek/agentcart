import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantUpdate


def create_merchant(db: Session, merchant_in: MerchantCreate) -> Merchant:
    """Create a new merchant after validating email uniqueness."""
    existing = db.execute(
        select(Merchant).where(Merchant.email == merchant_in.email)
    ).scalar_one_or_none()
    if existing:
        raise BadRequestException(
            message=f"Merchant with email '{merchant_in.email}' already exists."
        )

    merchant = Merchant(
        name=merchant_in.name,
        business_name=merchant_in.business_name,
        description=merchant_in.description,
        email=merchant_in.email,
        currency=merchant_in.currency,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def get_merchant(db: Session, merchant_id: uuid.UUID) -> Merchant:
    """Retrieve merchant by ID or raise NotFoundException."""
    merchant = db.execute(
        select(Merchant).where(Merchant.id == merchant_id)
    ).scalar_one_or_none()
    if not merchant:
        raise NotFoundException(message=f"Merchant '{merchant_id}' not found.")
    return merchant


def update_merchant(
    db: Session, merchant_id: uuid.UUID, merchant_in: MerchantUpdate
) -> Merchant:
    """Update merchant fields."""
    merchant = get_merchant(db, merchant_id)

    update_data = merchant_in.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != merchant.email:
        existing = db.execute(
            select(Merchant).where(Merchant.email == update_data["email"])
        ).scalar_one_or_none()
        if existing:
            raise BadRequestException(
                message=f"Email '{update_data['email']}' is already in use by another merchant."
            )

    for field, value in update_data.items():
        setattr(merchant, field, value)

    db.commit()
    db.refresh(merchant)
    return merchant
