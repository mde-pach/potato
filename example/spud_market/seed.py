"""Seed the database with sample farmers and products."""

import hashlib
from datetime import datetime, timezone

from example.spud_market.database import SessionLocal
from example.spud_market.infrastructure.db_models import FarmerRow, ProductRow


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data() -> None:
    """Insert sample data if the database is empty."""
    db = SessionLocal()
    try:
        if db.query(FarmerRow).first():
            return  # already seeded

        farmers = [
            FarmerRow(
                username="green_acres",
                email="alice@greenacres.farm",
                display_name="Green Acres Farm",
                password_hash=_hash("alice123"),
                street="123 Farm Road",
                city="Portland",
                state="OR",
                zip_code="97201",
                joined_at=datetime(2024, 3, 15, tzinfo=timezone.utc),
            ),
            FarmerRow(
                username="sunny_fields",
                email="bob@sunnyfields.farm",
                display_name="Sunny Fields Ranch",
                password_hash=_hash("bob456"),
                street="456 Country Lane",
                city="Eugene",
                state="OR",
                zip_code="97401",
                joined_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            ),
        ]
        db.add_all(farmers)
        db.flush()

        products = [
            ProductRow(
                name="Honeycrisp Apple",
                price_per_kg=3.49,
                description="Sweet and crunchy, straight from the orchard.",
                stock_kg=120.0,
                category="Fruit",
                farmer_id=farmers[0].id,
                listed_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
            ),
            ProductRow(
                name="Organic Carrots",
                price_per_kg=2.99,
                description="Freshly harvested, no pesticides.",
                stock_kg=80.0,
                category="Vegetable",
                farmer_id=farmers[0].id,
                listed_at=datetime(2025, 2, 5, tzinfo=timezone.utc),
            ),
            ProductRow(
                name="Heritage Tomato",
                price_per_kg=5.99,
                description="Heirloom variety, bursting with flavor.",
                stock_kg=45.0,
                category="Vegetable",
                farmer_id=farmers[1].id,
                listed_at=datetime(2025, 3, 20, tzinfo=timezone.utc),
            ),
            ProductRow(
                name="Fresh Strawberries",
                price_per_kg=7.49,
                description="Hand-picked this morning.",
                stock_kg=30.0,
                category="Fruit",
                farmer_id=farmers[1].id,
                listed_at=datetime(2025, 4, 1, tzinfo=timezone.utc),
            ),
        ]
        db.add_all(products)
        db.commit()
    finally:
        db.close()
