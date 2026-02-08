# Step 6: The Complete Spud Market

Here's the entire Spud Market application — every domain model, DTO, service, and route in one place. This is the same code that lives in `example/spud_market/`.

## Running the application

```bash
# From the project root
pip install fastapi uvicorn sqlalchemy pydantic-settings

# Start the server
uvicorn example.spud_market.main:app --reload

# Open the interactive docs
open http://localhost:8000/docs
```

The app creates a SQLite database (`spud_market.db`), seeds it with sample farmers and products, and starts the API. The Swagger UI at `/docs` lets you test every endpoint.

## Domain models

```python title="domain/models.py"
from datetime import datetime
from potato import Auto, Domain, Private


class FarmAddress(Domain):
    street: str
    city: str
    state: str
    zip_code: str


class Farmer(Domain):
    id: Auto[int]
    username: str
    email: str
    display_name: str
    password_hash: Private[str]
    farm_address: FarmAddress
    joined_at: Auto[datetime]


class Product(Domain):
    id: Auto[int]
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int
    listed_at: Auto[datetime]


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

```python title="domain/aggregates.py"
from potato import Aggregate


class ProductListing(Aggregate):
    product: Product
    farmer: Farmer


class OrderDetail(Aggregate):
    order: Order
    items: list[OrderItem]
```

## ViewDTOs

```python title="application/dtos.py"
from potato import ViewDTO, BuildDTO, Field, computed, before_build, after_build


class ProductSummary(ViewDTO[Product]):
    id: int
    name: str
    price_per_kg: float
    category: str

    @computed
    def display_price(self, product: Product) -> str:
        return f"${product.price_per_kg:.2f}/kg"


class ProductDetail(ProductSummary):
    description: str
    stock_kg: float
    farmer_id: int
    listed_at: str = Field(
        source=Product.listed_at,
        transform=lambda dt: dt.isoformat(),
    )

    @computed
    def in_stock(self, product: Product) -> bool:
        return product.stock_kg > 0


class ProductListingView(ViewDTO[ProductListing]):
    id: int = Field(source=ProductListing.product.id)
    name: str = Field(source=ProductListing.product.name)
    price_per_kg: float = Field(source=ProductListing.product.price_per_kg)
    category: str = Field(source=ProductListing.product.category)
    farmer_name: str = Field(source=ProductListing.farmer.display_name)
    farmer_city: str = Field(source=ProductListing.farmer.farm_address.city)

    @computed
    def display_price(self, agg: ProductListing) -> str:
        return f"${agg.product.price_per_kg:.2f}/kg"


class FarmerView(ViewDTO[Farmer]):
    id: int
    handle: str = Field(source=Farmer.username)
    display_name: str
    city: str = Field(source=Farmer.farm_address.city)
    state: str = Field(source=Farmer.farm_address.state)
    email: str = Field(visible=lambda ctx: ctx.is_admin)

    @computed
    def member_since(self, farmer: Farmer) -> str:
        return farmer.joined_at.strftime("%B %Y")


class OrderItemView(ViewDTO[OrderItem]):
    product_name: str
    quantity_kg: float
    unit_price: float

    @computed
    def line_total(self, item: OrderItem) -> float:
        return round(item.quantity_kg * item.unit_price, 2)


class OrderView(ViewDTO[Order]):
    id: int
    customer_name: str
    status: str
    placed_at: str = Field(
        source=Order.placed_at,
        transform=lambda dt: dt.isoformat(),
    )


class OrderDetailView(ViewDTO[OrderDetail]):
    order_id: int = Field(source=OrderDetail.order.id)
    customer_name: str = Field(source=OrderDetail.order.customer_name)
    customer_email: str = Field(source=OrderDetail.order.customer_email)
    status: str = Field(source=OrderDetail.order.status)
    items: list[OrderItemView]
    item_count: int
    computed_total: float

    @before_build
    def enrich(cls, entity: OrderDetail) -> dict:
        return {
            "item_count": len(entity.items),
            "computed_total": round(
                sum(i.quantity_kg * i.unit_price for i in entity.items), 2
            ),
        }

    @after_build
    def validate_total(self) -> None:
        if self.computed_total <= 0:
            raise ValueError(
                f"Order {self.order_id} has invalid total: {self.computed_total}"
            )
```

## BuildDTOs

```python title="application/dtos.py (continued)"
import hashlib


class FarmerCreate(BuildDTO[Farmer]):
    username: str
    email: str
    display_name: str
    password: str                # not on Farmer — used in to_domain() override
    farm_address: FarmAddress

    def to_domain(self, **kwargs) -> Farmer:
        kwargs.setdefault(
            "password_hash", hashlib.sha256(self.password.encode()).hexdigest()
        )
        return super().to_domain(**kwargs)


class ProductCreate(BuildDTO[Product]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int


class ProductUpdate(BuildDTO[Product], partial=True, exclude=[Product.farmer_id]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    # farmer_id excluded — can't be changed via PATCH
```

## API endpoints

| Method | Path | Description | DTO |
|--------|------|-------------|-----|
| GET | `/api/products` | List all products | `list[ProductSummary]` |
| GET | `/api/products/listings` | Products with farmer info | `list[ProductListingView]` |
| GET | `/api/products/{id}` | Product detail | `ProductDetail` |
| POST | `/api/products` | Create product | `ProductCreate` → `ProductDetail` |
| PATCH | `/api/products/{id}` | Update product | `ProductUpdate` → `ProductDetail` |
| DELETE | `/api/products/{id}` | Delete product | — |
| GET | `/api/farmers` | List farmers | `list[FarmerView]` |
| POST | `/api/farmers` | Create farmer | `FarmerCreate` → `FarmerView` |
| GET | `/api/farmers/{id}` | Farmer profile | `FarmerView` |
| GET | `/api/orders` | List orders | `list[OrderView]` |
| GET | `/api/orders/{id}` | Order detail | `OrderDetailView` |
| POST | `/api/orders` | Place order | Input → `OrderDetailView` |

## Quick test

```bash
# List products
curl http://localhost:8000/api/products
# [{"id":1,"name":"Honeycrisp Apple","price_per_kg":3.49,"category":"Fruit","display_price":"$3.49/kg"}, ...]

# Browse marketplace (products + farmer info + deep flattening)
curl http://localhost:8000/api/products/listings
# [{"id":1,"name":"Honeycrisp Apple","price_per_kg":3.49,"category":"Fruit",
#   "farmer_name":"Green Acres Farm","farmer_city":"Portland","display_price":"$3.49/kg"}, ...]

# Create a product (Auto fields excluded from input)
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Wild Mushrooms","price_per_kg":12.99,"description":"Foraged locally.",
       "stock_kg":10.0,"category":"Specialty","farmer_id":1}'
# {"id":5,"name":"Wild Mushrooms","price_per_kg":12.99,"category":"Specialty",
#  "display_price":"$12.99/kg","description":"Foraged locally.","stock_kg":10.0,
#  "farmer_id":1,"listed_at":"2025-...","in_stock":true}

# Partial update
curl -X PATCH http://localhost:8000/api/products/5 \
  -H "Content-Type: application/json" \
  -d '{"price_per_kg": 14.99}'
# price_per_kg changed, everything else unchanged

# Farmer — public (no email)
curl http://localhost:8000/api/farmers/1
# {"id":1,"handle":"green_acres","display_name":"Green Acres Farm","city":"Portland","state":"OR","member_since":"March 2024"}

# Farmer — admin (email included)
curl "http://localhost:8000/api/farmers/1?is_admin=true"
# {"id":1,"handle":"green_acres","display_name":"Green Acres Farm","city":"Portland","state":"OR","email":"alice@greenacres.farm","member_since":"March 2024"}

# Place an order (nested ViewDTOs + hooks)
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Jane Doe","customer_email":"jane@example.com",
       "items":[{"product_id":1,"quantity_kg":2.0},{"product_id":2,"quantity_kg":1.5}]}'
# {"order_id":1,"customer_name":"Jane Doe","customer_email":"jane@example.com",
#  "status":"pending","item_count":2,"computed_total":11.47,
#  "items":[{"product_name":"Honeycrisp Apple","quantity_kg":2.0,"unit_price":3.49,"line_total":6.98},
#           {"product_name":"Organic Carrots","quantity_kg":1.5,"unit_price":2.99,"line_total":4.49}]}
```

## Concept recap

| Concept | Where it appears |
|---------|-----------------|
| `Domain` | `Product`, `Farmer`, `FarmAddress`, `Order`, `OrderItem` |
| `Auto[T]` / `UNASSIGNED` | `id`, `listed_at`, `placed_at`, `joined_at` — default to `UNASSIGNED`, assigned by infrastructure |
| `Private[T]` | `Farmer.password_hash` — never exposed in any ViewDTO |
| `ViewDTO` | `ProductSummary`, `ProductDetail`, `FarmerView`, `OrderItemView`, `OrderView`, `OrderDetailView`, `ProductListingView` |
| `BuildDTO` | `ProductCreate`, `ProductUpdate`, `FarmerCreate` |
| `from_domain()` / `from_domains()` | Every read path: domain → view |
| `to_domain()` | Product creation: input → domain |
| `apply_to()` | Product updates: partial input + existing → new domain |
| `@computed` | `display_price`, `in_stock`, `line_total`, `member_since` |
| `Field(source=...)` | `FarmerView.handle`, all aggregate view fields |
| `Field(transform=...)` | `ProductDetail.listed_at`, `OrderView.placed_at` — datetime → ISO string |
| `Field(visible=...)` | `FarmerView.email` — admin-only |
| ViewDTO inheritance | `ProductDetail` extends `ProductSummary` |
| `Aggregate` | `ProductListing`, `OrderDetail` |
| Deep flattening | `FarmerView.city`, `ProductListingView.farmer_city` |
| Nested ViewDTOs | `OrderDetailView.items: list[OrderItemView]` |
| `@before_build` | `OrderDetailView.enrich` — compute totals |
| `@after_build` | `OrderDetailView.validate_total` — validate result |
| `partial=True` | `ProductUpdate` — PATCH with only changed fields |
| `exclude=` | `ProductUpdate` — `farmer_id` can't be changed via PATCH |
| Non-domain fields | `FarmerCreate.password` — filtered by `to_domain()`, used in override |
| `to_domain()` override | `FarmerCreate` — hash password before domain creation |
| Error messages | Class-definition-time validation with hints |

---

[:material-arrow-left: Previous: Access Control & Errors](step-05-access-control-and-errors.md){ .md-button }
[Back to Tutorial Overview](index.md){ .md-button .md-button--primary }
