from decimal import Decimal
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.models.buyer_policy import BuyerPolicy
from app.models.cart import Cart
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.policies.decisions import DecisionType
from app.policies.engine import evaluate_transaction_policies
from app.services.audit_service import record_audit_event
from app.services.cart_service import calculate_cart_totals, get_cart
from app.services.merchant_policy_service import get_merchant_policy


def create_order_from_cart(
    db: Session,
    merchant_id: UUID,
    cart_id: UUID,
    actor_id: str,
    idempotency_key: Optional[str] = None,
) -> Tuple[Order, Optional[list]]:
    """Create an Order from a Cart, handling idempotency, snapshotting, and policy evaluation."""
    # 1. Idempotency Check: if idempotency key provided, check for existing order
    if idempotency_key:
        existing_order = (
            db.query(Order)
            .filter(
                Order.merchant_id == merchant_id,
                Order.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing_order:
            return existing_order, None

    # 2. Retrieve & Validate Cart
    cart = get_cart(db, merchant_id, cart_id)
    if cart.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create order from cart with status '{cart.status}'",
        )

    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create order from an empty cart",
        )

    # 3. Re-verify inventory & products
    for item in cart.items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id, Product.merchant_id == merchant_id)
            .first()
        )
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product in cart is no longer active or available",
            )

        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == item.product_id)
            .first()
        )
        if inventory and item.quantity > inventory.available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for product '{product.name}'. "
                    f"Required {item.quantity}, available {inventory.available_quantity}."
                ),
            )

    # 4. Calculate Totals
    totals = calculate_cart_totals(cart)
    subtotal = totals["subtotal"]
    discount_total = totals["discount_total"]
    tax_total = totals["tax_total"]
    total = totals["total"]

    discount_percent = Decimal("0.00")
    if subtotal > Decimal("0.00"):
        discount_percent = (discount_total / subtotal) * Decimal("100.00")

    # 5. Fetch Policies & Evaluate Policy Engine
    merchant_policy = get_merchant_policy(db, merchant_id)
    buyer_policy = (
        db.query(BuyerPolicy)
        .filter(
            BuyerPolicy.merchant_id == merchant_id,
            BuyerPolicy.customer_identifier == cart.customer_identifier,
        )
        .first()
    )


    decision = evaluate_transaction_policies(
        merchant_policy=merchant_policy,
        buyer_policy=buyer_policy,
        amount=total,
        discount_percent=discount_percent,
        has_cross_sell=False,
        has_upsell=False,
        buyer_confirmation_provided=True,
    )

    # Determine initial Order & Policy & Approval Status
    if decision.decision == DecisionType.BLOCK:
        order_status = "CANCELLED"
        policy_status = "BLOCKED"
        approval_status = "NOT_REQUIRED"
    elif decision.decision == DecisionType.ALLOW_WITH_APPROVAL:
        order_status = "AWAITING_APPROVAL"
        policy_status = "APPROVAL_REQUIRED"
        approval_status = "PENDING"
    else:  # ALLOW
        order_status = "APPROVED"
        policy_status = "ALLOWED"
        approval_status = "NOT_REQUIRED"

    # 6. Create Order instance
    order = Order(
        merchant_id=merchant_id,
        cart_id=cart.id,
        customer_identifier=cart.customer_identifier,
        status=order_status,
        currency=cart.currency,
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total=total,
        policy_status=policy_status,
        approval_status=approval_status,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.flush()  # Assign order.id

    # 7. Create OrderItems with Snapshots
    for item in cart.items:
        product = db.get(Product, item.product_id)

        line_total = (item.unit_price * Decimal(item.quantity)) - item.discount_amount
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            sku_snapshot=product.sku,
            unit_price=item.unit_price,
            quantity=item.quantity,
            discount_amount=item.discount_amount,
            line_total=max(Decimal("0.00"), line_total),
        )
        db.add(order_item)

    # 8. Create Approval record if approval is required
    if decision.decision == DecisionType.ALLOW_WITH_APPROVAL:
        approval_entry = Approval(
            merchant_id=merchant_id,
            order_id=order.id,
            requested_amount=total,
            status="PENDING",
            reason=", ".join(decision.reasons),
        )
        db.add(approval_entry)

    # 9. Update Cart status
    if decision.decision == DecisionType.BLOCK:
        cart.status = "ABANDONED"
    else:
        cart.status = "CHECKOUT_PENDING"

    db.commit()
    db.refresh(order)

    # 10. Audit Logging
    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="order_created",
        resource_type="Order",
        resource_id=str(order.id),
        merchant_id=merchant_id,
        policy_decision=decision.decision.value,
        approval_status=approval_status,
        idempotency_key=idempotency_key,
        metadata={"total": str(total), "status": order_status},
    )

    record_audit_event(
        db=db,
        actor_type="SYSTEM",
        actor_id="policy_engine",
        action="policy_decision",
        resource_type="Order",
        resource_id=str(order.id),
        merchant_id=merchant_id,
        policy_decision=decision.decision.value,
        approval_status=approval_status,
        reason=", ".join(decision.reasons) if decision.reasons else None,
        metadata={
            "violations": decision.violations,
            "reasons": decision.reasons,
        },
    )

    if decision.decision == DecisionType.BLOCK:
        record_audit_event(
            db=db,
            actor_type="SYSTEM",
            actor_id="policy_engine",
            action="blocked_order",
            resource_type="Order",
            resource_id=str(order.id),
            merchant_id=merchant_id,
            policy_decision="BLOCK",
            reason=", ".join(decision.violations),
        )

    if decision.decision == DecisionType.ALLOW_WITH_APPROVAL:
        record_audit_event(
            db=db,
            actor_type="SYSTEM",
            actor_id="policy_engine",
            action="approval_required",
            resource_type="Order",
            resource_id=str(order.id),
            merchant_id=merchant_id,
            approval_status="PENDING",
            reason=", ".join(decision.reasons),
        )

    violations_list = decision.violations if decision.violations else None
    return order, violations_list


def get_order(db: Session, merchant_id: UUID, order_id: UUID) -> Order:
    """Retrieve an order by ID ensuring merchant scoping."""
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
    return order
