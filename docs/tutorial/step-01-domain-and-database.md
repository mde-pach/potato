# Step 1: Domain Models & Database

Every application starts with the domain layer — the core business objects. In this step, we'll create all the domain models for Spud Market and wire them to a SQLite database through SQLAlchemy.

## The domain models

Potato's `Domain` base class builds on Pydantic. You get validation, serialization, and integration with Potato's DTO system. Let's model our marketplace.

### Products and addresses

```python title="domain/models.py"
from datetime import datetime
from potato import Auto, Domain, Private


class FarmAddress(Domain):
    street: str
    city: str
    state: str
    zip_code: str


class Product(Domain):
    id: Auto[int]
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int
    listed_at: Auto[datetime]
```

Two markers appear here that are central to Potato:

**`Auto[T]`** — marks fields managed by the system, not the user. `id` comes from the database's autoincrement. `listed_at` is set by the service layer. Auto fields default to `UNASSIGNED` — a sentinel that raises `AttributeError` if you accidentally try to use it (compare, serialize, cast). This means you can create a domain model without providing Auto values, and the infrastructure layer fills them in later. When we build DTOs later, Potato will automatically exclude these from input forms while including them in output views.

**`FarmAddress`** — a value object nested inside `Farmer`. Potato can flatten nested domains into ViewDTO fields, which we'll use in Step 3.

### Farmers

```python title="domain/models.py (continued)"
class Farmer(Domain):
    id: Auto[int]
    username: str
    email: str
    display_name: str
    password_hash: Private[str]
    farm_address: FarmAddress
    joined_at: Auto[datetime]
```

**`Private[T]`** — marks fields that must never appear in any API response. Unlike `Auto` (excluded from input, included in output), `Private` fields are forbidden in ViewDTOs entirely. If you try to expose `password_hash` in a view, Potato raises a `TypeError` at class definition time — before your app even starts.

### Orders

```python title="domain/models.py (continued)"
class Order(Domain):
    id: Auto[int]
    customer_name: str
    customer_email: str
    status: str = "pending"
    placed_at: Auto[datetime]


class OrderItem(Domain):
    id: Auto[int]
    order_id: int
    product_name: str
    quantity_kg: float
    unit_price: float
```

## Aggregates

Orders span multiple domains — an order has line items. Potato's `Aggregate` composes domains by declaring them as fields:

```python title="domain/aggregates.py"
from potato import Aggregate
from .models import Farmer, Order, OrderItem, Product


class ProductListing(Aggregate):
    """A product with its farmer — for marketplace listings."""
    product: Product
    farmer: Farmer


class OrderDetail(Aggregate):
    """An order with its line items."""
    order: Order
    items: list[OrderItem]
```

Field names on the aggregate (`product`, `farmer`, `order`, `items`) become namespaces for accessing sub-domain fields in ViewDTOs. We'll use this in Step 4.

## The database layer

Domain models are pure business objects — they don't know about databases. We bridge the gap with SQLAlchemy models, mappers, and repositories.

### SQLAlchemy models

```python title="infrastructure/db_models.py"
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class FarmerRow(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # FarmAddress fields are flattened into the row
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    products: Mapped[list["ProductRow"]] = relationship(back_populates="farmer")


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    stock_kg: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id"), nullable=False)
    listed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    farmer: Mapped["FarmerRow"] = relationship(back_populates="products")
```

Notice that `id` uses `autoincrement=True` — this is where Auto IDs actually come from. The database generates them, the repository reads them back, and the domain model carries them. Potato's `Auto[T]` marker ensures that no input DTO will ever ask the user to provide one.

### Mappers

Mappers convert between domain models and database rows:

```python title="infrastructure/mappers.py"
def farmer_row_to_domain(row: FarmerRow) -> Farmer:
    return Farmer(
        id=row.id,
        username=row.username,
        email=row.email,
        display_name=row.display_name,
        password_hash=row.password_hash,
        farm_address=FarmAddress(
            street=row.street, city=row.city,
            state=row.state, zip_code=row.zip_code,
        ),
        joined_at=row.joined_at,
    )

def product_row_to_domain(row: ProductRow) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        price_per_kg=row.price_per_kg,
        description=row.description,
        stock_kg=row.stock_kg,
        category=row.category,
        farmer_id=row.farmer_id,
        listed_at=row.listed_at,
    )
```

### Repositories

Repositories encapsulate data access. Here's the product repository:

```python title="infrastructure/repositories.py"
class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, product: Product) -> Product:
        row = product_domain_to_row(product)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)        # ← database assigns the id here
        return product_row_to_domain(row) # ← domain model now has a real id

    def get_by_id(self, product_id: int) -> Product | None:
        row = self.session.get(ProductRow, product_id)
        return product_row_to_domain(row) if row else None

    def update(self, product: Product) -> Product:
        row = self.session.get(ProductRow, product.id)
        if not row:
            raise ValueError(f"Product {product.id} not found")
        product_domain_to_row(product, row)
        self.session.commit()
        self.session.refresh(row)
        return product_row_to_domain(row)
```

The `create` method shows the full Auto field lifecycle: the domain is constructed with `id` left as `UNASSIGNED` (the default for Auto fields), the database assigns the real ID via autoincrement, and the mapper reads it back into a domain model with the real ID. If you accidentally try to use an `UNASSIGNED` value (e.g. `product.id > 0`), you'll get a clear `AttributeError` explaining what happened.

### Seed data

A seed script populates the database with sample farmers and products:

```python title="seed.py"
def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(FarmerRow).first():
            return  # already seeded

        farmers = [
            FarmerRow(
                username="green_acres",
                email="alice@greenacres.farm",
                display_name="Green Acres Farm",
                password_hash=hashlib.sha256(b"alice123").hexdigest(),
                street="123 Farm Road",
                city="Portland", state="OR", zip_code="97201",
                joined_at=datetime(2024, 3, 15, tzinfo=timezone.utc),
            ),
            # ... more farmers
        ]
        db.add_all(farmers)
        db.flush()

        products = [
            ProductRow(
                name="Honeycrisp Apple", price_per_kg=3.49,
                description="Sweet and crunchy, straight from the orchard.",
                stock_kg=120.0, category="Fruit",
                farmer_id=farmers[0].id,
            ),
            # ... more products
        ]
        db.add_all(products)
        db.commit()
    finally:
        db.close()
```

!!! info "What we built"
    - 5 domain models (`Product`, `Farmer`, `FarmAddress`, `Order`, `OrderItem`)
    - 2 aggregates (`ProductListing`, `OrderDetail`)
    - SQLAlchemy models with autoincrement IDs
    - Mappers and repositories
    - Seed data with 2 farmers and 4 products

    **Potato concepts introduced:** `Domain`, `Auto[T]`, `Private[T]`, `Aggregate`

---

[Next: Step 2 — The Product API :material-arrow-right:](step-02-product-api.md){ .md-button }
