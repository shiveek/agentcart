import os
import sys
from decimal import Decimal

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy.orm import Session

from app.db.database import Base, engine
from app.db.session import SessionLocal
from app.schemas.merchant import MerchantCreate
from app.schemas.product import ProductCreate
from app.schemas.relationship import ProductRelationshipCreate
from app.services.merchant_service import create_merchant
from app.services.product_service import create_product
from app.services.relationship_service import create_product_relationship


def seed_database() -> None:
    """Seed the database with TechNest demo merchant, products, and relationships."""
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Seeding demo merchant 'TechNest'...")
        merchant_in = MerchantCreate(
            name="TechNest",
            business_name="TechNest Electronics Pvt Ltd",
            description="Premium computer accessories, ergonomics, and desk gear for professionals.",
            email="contact@technest.io",
            currency="INR",
        )
        try:
            merchant = create_merchant(db, merchant_in)
            print(f"[OK] Created Merchant: {merchant.name} (ID: {merchant.id})")
        except Exception:
            from sqlalchemy import select
            from app.models.merchant import Merchant
            merchant = db.execute(select(Merchant).where(Merchant.email == "contact@technest.io")).scalar_one()
            print(f"[INFO] Merchant '{merchant.name}' already exists (ID: {merchant.id}).")

        print("\nSeeding products...")
        products_data = [
            {
                "sku": "KB001",
                "name": "Mechanical Keyboard",
                "description": "Tactile RGB mechanical keyboard with custom switches and aluminum frame.",
                "category": "Keyboard",
                "price": Decimal("2499.00"),
                "stock": 42,
            },
            {
                "sku": "MS001",
                "name": "Wireless Mouse",
                "description": "Ergonomic 2.4GHz wireless optical mouse with silent click buttons.",
                "category": "Mouse",
                "price": Decimal("699.00"),
                "stock": 75,
            },
            {
                "sku": "LS001",
                "name": "Laptop Stand",
                "description": "Adjustable aluminum laptop riser stand with ventilation cooling.",
                "category": "Laptop Accessories",
                "price": Decimal("1499.00"),
                "stock": 25,
            },
            {
                "sku": "HUB001",
                "name": "USB-C Hub",
                "description": "7-in-1 USB-C adapter hub with 4K HDMI, USB 3.0, and 100W Power Delivery.",
                "category": "Accessories",
                "price": Decimal("999.00"),
                "stock": 50,
            },
            {
                "sku": "CAM001",
                "name": "Webcam",
                "description": "1080p Full HD streaming webcam with dual noise-canceling microphones.",
                "category": "Webcam",
                "price": Decimal("2199.00"),
                "stock": 30,
            },
            {
                "sku": "HP001",
                "name": "Headphones",
                "description": "Wireless over-ear active noise canceling headphones with 30-hour battery life.",
                "category": "Audio",
                "price": Decimal("2799.00"),
                "stock": 20,
            },
        ]

        created_products = {}
        for p in products_data:
            p_in = ProductCreate(
                sku=p["sku"],
                name=p["name"],
                description=p["description"],
                category=p["category"],
                price=p["price"],
                currency="INR",
                initial_quantity=p["stock"],
            )
            try:
                prod = create_product(db, merchant.id, p_in)
                created_products[p["sku"]] = prod
                print(f"  [OK] Created Product: {prod.name} [{prod.sku}] - INR {prod.price} (Stock: {p['stock']})")
            except Exception:
                from sqlalchemy import select
                from app.models.product import Product
                prod = db.execute(
                    select(Product).where(Product.merchant_id == merchant.id, Product.sku == p["sku"])
                ).scalar_one()
                created_products[p["sku"]] = prod
                print(f"  [INFO] Product [{p['sku']}] already exists.")

        print("\nSeeding product relationships...")
        relationships_data = [
            {
                "source_sku": "KB001",
                "target_sku": "MS001",
                "type": "cross_sell",
                "score": Decimal("0.87"),
                "reason": "Popular desk combo bundle",
            },
            {
                "source_sku": "KB001",
                "target_sku": "LS001",
                "type": "frequently_bought_together",
                "score": Decimal("0.61"),
                "reason": "Ergonomic work-from-home setup",
            },
            {
                "source_sku": "LS001",
                "target_sku": "HUB001",
                "type": "cross_sell",
                "score": Decimal("0.72"),
                "reason": "Essential connectivity accessory for laptop stands",
            },
            {
                "source_sku": "CAM001",
                "target_sku": "HP001",
                "type": "frequently_bought_together",
                "score": Decimal("0.48"),
                "reason": "Video conferencing and meeting bundle",
            },
        ]

        for rel in relationships_data:
            source = created_products[rel["source_sku"]]
            target = created_products[rel["target_sku"]]

            rel_in = ProductRelationshipCreate(
                target_product_id=target.id,
                relationship_type=rel["type"],
                score=rel["score"],
                reason=rel["reason"],
            )
            created_rel = create_product_relationship(db, source.id, rel_in)
            print(f"  [OK] Created Relationship: {source.name} -> {target.name} ({rel['type']} | score: {rel['score']})")

        print(f"\nSuccessfully seeded demo data for Merchant '{merchant.name}' (ID: {merchant.id})!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
