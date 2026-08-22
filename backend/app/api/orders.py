from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_current_user
from app.db.session import get_db
from app.models.approval import Approval
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.approval import ApprovalAction, ApprovalResponse
from app.schemas.order import OrderResponse
from app.services.approval_service import approve_order, reject_order
from app.services.order_service import create_order_from_cart, get_order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/from-cart/{cart_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from active cart",
    description=(
        "Converts an active cart into an immutable Order with product snapshots, "
        "re-calculates totals, and evaluates merchant and buyer policy engines. "
        "Supports idempotent requests via Idempotency-Key header."
    ),
)
def create_order(
    cart_id: UUID,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    key = idempotency_key or x_idempotency_key
    order, violations = create_order_from_cart(
        db=db,
        merchant_id=current_merchant.id,
        cart_id=cart_id,
        actor_id=str(current_user.id),
        idempotency_key=key,
    )
    
    response = OrderResponse.model_validate(order)
    if violations:
        response.violations = violations
    return response


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Retrieve details, policy status, and line items for an order.",
)
def get_order_endpoint(
    order_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> OrderResponse:
    order = get_order(db=db, merchant_id=current_merchant.id, order_id=order_id)
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve pending order",
    description="Approve an order that is in AWAITING_APPROVAL status.",
)
def approve_order_endpoint(
    order_id: UUID,
    action: Optional[ApprovalAction] = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Approval:
    reason = action.reason if action else None
    return approve_order(
        db=db,
        merchant_id=current_merchant.id,
        order_id=order_id,
        user_id=current_user.id,
        reason=reason,
    )


@router.post(
    "/{order_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject pending order",
    description="Reject an order that is in AWAITING_APPROVAL status.",
)
def reject_order_endpoint(
    order_id: UUID,
    action: Optional[ApprovalAction] = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Approval:
    reason = action.reason if action else None
    return reject_order(
        db=db,
        merchant_id=current_merchant.id,
        order_id=order_id,
        user_id=current_user.id,
        reason=reason,
    )
