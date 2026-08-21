import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import InventoryUpdate


def get_inventory_by_product_id(db: Session, product_id: uuid.UUID) -> Inventory:
    """Retrieve inventory record for a product or raise NotFoundException."""
    product = db.execute(
        select(Product).where(Product.id == product_id)
    ).scalar_one_or_none()
    if not product:
        raise NotFoundException(message=f"Product '{product_id}' not found.")

    inventory = db.execute(
        select(Inventory).where(Inventory.product_id == product_id)
    ).scalar_one_or_none()

    if not inventory:
        # Auto-create empty inventory if missing
        inventory = Inventory(
            product_id=product_id, quantity=0, reserved_quantity=0, reorder_level=0
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

    return inventory


def update_inventory(
    db: Session, product_id: uuid.UUID, inventory_in: InventoryUpdate
) -> Inventory:
    """Update inventory counts for a product."""
    inventory = get_inventory_by_product_id(db, product_id)

    if inventory_in.reserved_quantity > inventory_in.quantity:
        raise BadRequestException(
            message=f"reserved_quantity ({inventory_in.reserved_quantity}) cannot exceed total quantity ({inventory_in.quantity})."
        )

    inventory.quantity = inventory_in.quantity
    inventory.reserved_quantity = inventory_in.reserved_quantity
    inventory.reorder_level = inventory_in.reorder_level

    db.commit()
    db.refresh(inventory)
    return inventory
