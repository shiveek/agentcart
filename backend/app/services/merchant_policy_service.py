from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.merchant_policy import MerchantPolicy
from app.schemas.policy import MerchantPolicyUpdate
from app.services.audit_service import record_audit_event


def get_merchant_policy(db: Session, merchant_id: UUID) -> MerchantPolicy:
    """Retrieve existing merchant policy or initialize default policy."""
    policy = (
        db.query(MerchantPolicy)
        .filter(MerchantPolicy.merchant_id == merchant_id)
        .first()
    )
    if not policy:
        policy = MerchantPolicy(
            merchant_id=merchant_id,
            max_transaction_amount=Decimal("5000.00"),
            max_discount_percent=Decimal("10.00"),
            approval_threshold=Decimal("3000.00"),
            require_buyer_confirmation=True,
            allow_cross_sell=True,
            allow_upsell=True,
            max_payment_retries=1,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def update_merchant_policy(
    db: Session,
    merchant_id: UUID,
    policy_update: MerchantPolicyUpdate,
    actor_user_id: UUID,
) -> MerchantPolicy:
    """Update merchant policy with validation and audit logging."""
    policy = get_merchant_policy(db, merchant_id)

    update_data = policy_update.model_dump(exclude_unset=True)
    if not update_data:
        return policy

    # Pre-validate effective values after update
    new_max_amount = update_data.get("max_transaction_amount", policy.max_transaction_amount)
    new_threshold = update_data.get("approval_threshold", policy.approval_threshold)

    if new_threshold > new_max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="approval_threshold cannot exceed max_transaction_amount",
        )

    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=str(actor_user_id),
        action="merchant_policy_updated",
        resource_type="MerchantPolicy",
        resource_id=str(policy.id),
        merchant_id=merchant_id,
        metadata={"updated_fields": update_data},
    )

    return policy
