from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_current_user
from app.db.session import get_db
from app.models.cart import Cart, CartItem
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.cart import (
    CartCreate,
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
    CartSummaryResponse,
)
from app.services.cart_service import (
    add_cart_item,
    calculate_cart_totals,
    create_cart,
    get_cart,
    remove_cart_item,
    update_cart_item,
)

router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new merchant shopping cart",
    description="Create an active shopping cart for a specific customer associated with the authenticated merchant.",
)
def create_cart_endpoint(
    cart_in: CartCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Cart:
    return create_cart(
        db=db,
        merchant_id=current_merchant.id,
        cart_in=cart_in,
        actor_id=str(current_user.id),
    )


@router.get(
    "/{cart_id}",
    response_model=CartResponse,
    summary="Get cart details",
    description="Retrieve details and line items of a cart belonging to the authenticated merchant.",
)
def get_cart_endpoint(
    cart_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> Cart:
    return get_cart(db=db, merchant_id=current_merchant.id, cart_id=cart_id)


@router.post(
    "/{cart_id}/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product to an active cart. Unit price is fetched server-side from the database.",
)
def add_item_endpoint(
    cart_id: UUID,
    item_in: CartItemCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartItem:
    return add_cart_item(
        db=db,
        merchant_id=current_merchant.id,
        cart_id=cart_id,
        item_in=item_in,
        actor_id=str(current_user.id),
    )


@router.put(
    "/{cart_id}/items/{item_id}",
    response_model=CartItemResponse,
    summary="Update cart item quantity",
    description="Update quantity for an existing cart line item.",
)
def update_item_endpoint(
    cart_id: UUID,
    item_id: UUID,
    item_update: CartItemUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartItem:
    return update_cart_item(
        db=db,
        merchant_id=current_merchant.id,
        cart_id=cart_id,
        item_id=item_id,
        item_update=item_update,
        actor_id=str(current_user.id),
    )


@router.delete(
    "/{cart_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    description="Remove a product item from an active cart.",
)
def remove_item_endpoint(
    cart_id: UUID,
    item_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    remove_cart_item(
        db=db,
        merchant_id=current_merchant.id,
        cart_id=cart_id,
        item_id=item_id,
        actor_id=str(current_user.id),
    )


@router.get(
    "/{cart_id}/summary",
    response_model=CartSummaryResponse,
    summary="Get cart financial summary",
    description="Calculate subtotal, discounts, taxes, and total for a cart.",
)
def get_cart_summary_endpoint(
    cart_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> CartSummaryResponse:
    cart = get_cart(db=db, merchant_id=current_merchant.id, cart_id=cart_id)
    totals = calculate_cart_totals(cart)
    return CartSummaryResponse(
        cart_id=cart.id,
        items=cart.items,
        subtotal=totals["subtotal"],
        discount_total=totals["discount_total"],
        tax_total=totals["tax_total"],
        total=totals["total"],
        currency=totals["currency"],
    )
