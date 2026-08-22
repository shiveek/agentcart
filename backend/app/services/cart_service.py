from decimal import Decimal
from typing import Any, Dict, Tuple
from uuid import UUID


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.cart import CartCreate, CartItemCreate, CartItemUpdate
from app.services.audit_service import record_audit_event


def create_cart(
    db: Session,
    merchant_id: UUID,
    cart_in: CartCreate,
    actor_id: str,
) -> Cart:
    """Create a new shopping cart for a merchant and customer."""
    cart = Cart(
        merchant_id=merchant_id,
        customer_identifier=cart_in.customer_identifier,
        currency=cart_in.currency,
        status="ACTIVE",
    )
    db.add(cart)
    db.commit()
    db.refresh(cart)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="cart_created",
        resource_type="Cart",
        resource_id=str(cart.id),
        merchant_id=merchant_id,
        metadata={
            "customer_identifier": cart.customer_identifier,
            "currency": cart.currency,
        },
    )

    return cart


def get_cart(db: Session, merchant_id: UUID, cart_id: UUID) -> Cart:
    """Retrieve a cart and verify it belongs to the authenticated merchant."""
    cart = (
        db.query(Cart)
        .filter(Cart.id == cart_id, Cart.merchant_id == merchant_id)
        .first()
    )
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found or does not belong to merchant",
        )
    return cart


def add_cart_item(
    db: Session,
    merchant_id: UUID,
    cart_id: UUID,
    item_in: CartItemCreate,
    actor_id: str,
) -> CartItem:
    """Add a product item to an active cart with inventory and pricing checks."""
    cart = get_cart(db, merchant_id, cart_id)
    if cart.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add items to cart with status '{cart.status}'",
        )

    product = (
        db.query(Product)
        .filter(Product.id == item_in.product_id, Product.merchant_id == merchant_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or does not belong to merchant",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{product.name}' is inactive and cannot be added to cart",
        )

    # Check inventory
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.id)
        .first()
    )
    existing_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart_id, CartItem.product_id == product.id)
        .first()
    )
    existing_qty = existing_item.quantity if existing_item else 0
    requested_total_qty = existing_qty + item_in.quantity

    if inventory:
        available = inventory.available_quantity
        if requested_total_qty > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for product '{product.name}'. "
                    f"Requested total {requested_total_qty}, available {available}."
                ),
            )

    if existing_item:
        existing_item.quantity = requested_total_qty
        # Unit price is preserved or updated to current database product price if re-adding
        db.commit()
        db.refresh(existing_item)
        item = existing_item
    else:
        item = CartItem(
            cart_id=cart_id,
            product_id=product.id,
            quantity=item_in.quantity,
            unit_price=product.price,  # Server-side price lookup
            discount_amount=Decimal("0.00"),
        )
        db.add(item)
        db.commit()
        db.refresh(item)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="cart_item_added",
        resource_type="CartItem",
        resource_id=str(item.id),
        merchant_id=merchant_id,
        metadata={
            "cart_id": str(cart_id),
            "product_id": str(product.id),
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
        },
    )

    return item


def update_cart_item(
    db: Session,
    merchant_id: UUID,
    cart_id: UUID,
    item_id: UUID,
    item_update: CartItemUpdate,
    actor_id: str,
) -> CartItem:
    """Update quantity of an existing item in a cart."""
    cart = get_cart(db, merchant_id, cart_id)
    if cart.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update items in cart with status '{cart.status}'",
        )

    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart_id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    # Check inventory for updated quantity
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == item.product_id)
        .first()
    )
    if inventory and item_update.quantity > inventory.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock for product. "
                f"Requested {item_update.quantity}, available {inventory.available_quantity}."
            ),
        )

    item.quantity = item_update.quantity
    db.commit()
    db.refresh(item)
    return item


def remove_cart_item(
    db: Session,
    merchant_id: UUID,
    cart_id: UUID,
    item_id: UUID,
    actor_id: str,
) -> None:
    """Remove an item from a cart."""
    cart = get_cart(db, merchant_id, cart_id)
    if cart.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot remove items from cart with status '{cart.status}'",
        )

    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart_id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    product_id = item.product_id
    db.delete(item)
    db.commit()

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=actor_id,
        action="cart_item_removed",
        resource_type="CartItem",
        resource_id=str(item_id),
        merchant_id=merchant_id,
        metadata={"cart_id": str(cart_id), "product_id": str(product_id)},
    )


def calculate_cart_totals(cart: Cart) -> Dict[str, Any]:
    """Calculate financial totals (subtotal, discount_total, tax_total, total) for a cart using Decimal arithmetic."""
    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")

    for item in cart.items:
        item_subtotal = item.unit_price * Decimal(item.quantity)
        subtotal += item_subtotal
        discount_total += item.discount_amount

    tax_total = Decimal("0.00")
    total = subtotal - discount_total + tax_total

    return {
        "subtotal": subtotal,
        "discount_total": discount_total,
        "tax_total": tax_total,
        "total": max(Decimal("0.00"), total),
        "currency": cart.currency,
    }
