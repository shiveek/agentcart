from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.models.order import Order
from app.services.audit_service import record_audit_event


def approve_order(
    db: Session,
    merchant_id: UUID,
    order_id: UUID,
    user_id: UUID,
    reason: Optional[str] = None,
) -> Approval:
    """Approve an order in AWAITING_APPROVAL status."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.merchant_id == merchant_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be approved because current status is '{order.status}'",
        )

    approval = (
        db.query(Approval)
        .filter(Approval.order_id == order_id, Approval.merchant_id == merchant_id)
        .first()
    )
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval record not found for order",
        )

    now = datetime.now(timezone.utc)
    approval.status = "APPROVED"
    approval.decided_at = now
    approval.decided_by = user_id
    if reason:
        approval.reason = reason

    order.status = "APPROVED"
    order.approval_status = "APPROVED"

    db.commit()
    db.refresh(approval)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=str(user_id),
        action="order_approved",
        resource_type="Order",
        resource_id=str(order_id),
        merchant_id=merchant_id,
        approval_status="APPROVED",
        reason=reason,
    )

    return approval


def reject_order(
    db: Session,
    merchant_id: UUID,
    order_id: UUID,
    user_id: UUID,
    reason: Optional[str] = None,
) -> Approval:
    """Reject an order in AWAITING_APPROVAL status."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.merchant_id == merchant_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be rejected because current status is '{order.status}'",
        )

    approval = (
        db.query(Approval)
        .filter(Approval.order_id == order_id, Approval.merchant_id == merchant_id)
        .first()
    )
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval record not found for order",
        )

    now = datetime.now(timezone.utc)
    approval.status = "REJECTED"
    approval.decided_at = now
    approval.decided_by = user_id
    if reason:
        approval.reason = reason

    order.status = "CANCELLED"
    order.approval_status = "REJECTED"

    db.commit()
    db.refresh(approval)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=str(user_id),
        action="order_rejected",
        resource_type="Order",
        resource_id=str(order_id),
        merchant_id=merchant_id,
        approval_status="REJECTED",
        reason=reason,
    )

    return approval
