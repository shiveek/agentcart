import math
import uuid
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.merchant_service import get_merchant


def create_product(
    db: Session, merchant_id: uuid.UUID, product_in: ProductCreate
) -> Product:
    """Create a new product under a merchant and initialize inventory."""
    get_merchant(db, merchant_id)

    # Check for SKU uniqueness per merchant
    existing_sku = db.execute(
        select(Product).where(
            Product.merchant_id == merchant_id, Product.sku == product_in.sku
        )
    ).scalar_one_or_none()
    if existing_sku:
        raise BadRequestException(
            message=f"Product SKU '{product_in.sku}' already exists for this merchant."
        )

    product = Product(
        merchant_id=merchant_id,
        sku=product_in.sku,
        name=product_in.name,
        description=product_in.description,
        category=product_in.category,
        price=product_in.price,
        currency=product_in.currency,
        is_active=product_in.is_active,
    )
    db.add(product)
    db.flush()

    # Initialize associated inventory
    inventory = Inventory(
        product_id=product.id,
        quantity=product_in.initial_quantity,
        reserved_quantity=0,
        reorder_level=product_in.reorder_level,
    )
    db.add(inventory)

    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    """Retrieve product by ID with inventory loaded."""
    product = db.execute(
        select(Product)
        .options(selectinload(Product.inventory))
        .where(Product.id == product_id)
    ).scalar_one_or_none()
    if not product:
        raise NotFoundException(message=f"Product '{product_id}' not found.")
    return product


def list_products(
    db: Session,
    merchant_id: uuid.UUID,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[list[Product], int, int]:
    """List merchant products with filtering and pagination."""
    get_merchant(db, merchant_id)

    query = (
        select(Product)
        .options(selectinload(Product.inventory))
        .where(Product.merchant_id == merchant_id)
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Product.name.ilike(search_pattern))
            | (Product.description.ilike(search_pattern))
            | (Product.sku.ilike(search_pattern))
        )
    if category:
        query = query.where(Product.category.ilike(category))
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    # Count total matching items
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    # Pagination bounds
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    offset = (page - 1) * page_size
    items = (
        db.execute(query.order_by(Product.created_at.desc()).offset(offset).limit(page_size))
        .scalars()
        .all()
    )

    return list(items), total, total_pages


def update_product(
    db: Session, product_id: uuid.UUID, product_in: ProductUpdate
) -> Product:
    """Update product details."""
    product = get_product(db, product_id)
    update_data = product_in.model_dump(exclude_unset=True)

    if "sku" in update_data and update_data["sku"] != product.sku:
        existing_sku = db.execute(
            select(Product).where(
                Product.merchant_id == product.merchant_id,
                Product.sku == update_data["sku"],
                Product.id != product_id,
            )
        ).scalar_one_or_none()
        if existing_sku:
            raise BadRequestException(
                message=f"Product SKU '{update_data['sku']}' is already used by another product for this merchant."
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: uuid.UUID) -> Product:
    """Soft-delete / deactivate product."""
    product = get_product(db, product_id)
    product.is_active = False
    db.commit()
    db.refresh(product)
    return product
