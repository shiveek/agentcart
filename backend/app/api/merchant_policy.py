from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_current_user
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.merchant_policy import MerchantPolicy
from app.models.user import User
from app.schemas.policy import MerchantPolicyResponse, MerchantPolicyUpdate
from app.services.merchant_policy_service import (
    get_merchant_policy,
    update_merchant_policy,
)

router = APIRouter(prefix="/merchant/policy", tags=["Merchant Policy"])


@router.get(
    "",
    response_model=MerchantPolicyResponse,
    summary="Get merchant transaction and sales policy",
    description="Retrieve transaction limits, discount rules, and approval settings for the authenticated merchant.",
)
def get_policy(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantPolicy:
    return get_merchant_policy(db=db, merchant_id=current_merchant.id)


@router.put(
    "",
    response_model=MerchantPolicyResponse,
    summary="Update merchant transaction and sales policy",
    description="Update merchant policy limits and governance rules for the authenticated merchant.",
)
def update_policy(
    policy_update: MerchantPolicyUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MerchantPolicy:
    return update_merchant_policy(
        db=db,
        merchant_id=current_merchant.id,
        policy_update=policy_update,
        actor_user_id=current_user.id,
    )
