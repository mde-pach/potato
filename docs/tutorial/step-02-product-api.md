# Step 2: The Product API

With the domain and database in place, let's build the product API. This step introduces the core of Potato: transforming data between your domain layer and the outside world.

## Reading products — ViewDTOs

A ViewDTO transforms a domain object into a read-only external representation. You declare which fields to expose, and Potato handles the extraction.

### Product summary (list endpoint)

```python title="application/dtos.py"
from potato import ViewDTO, Field, computed


class ProductSummary(ViewDTO[Product]):
    """Compact view for product listings."""
    id: int
    name: str
    price_per_kg: float
    category: str

    @computed
    def display_price(self, product: Product) -> str:
        return f"${product.price_per_kg:.2f}/kg"
```

A few things to notice:

- **`ViewDTO[Product]`** binds this view to the `Product` domain. Fields are auto-mapped by name.
- **`@computed`** creates a derived field. The method receives the domain instance and returns the computed value. `display_price` doesn't exist in the domain — it's presentation logic that belongs in the view.
- **`stock_kg`, `listed_at`, `farmer_id`** are not listed — they won't appear in the summary.

### Product detail (single-item endpoint)

For the detail view, we want everything in the summary plus additional fields. Instead of duplicating, we inherit:

```python title="application/dtos.py (continued)"
class ProductDetail(ProductSummary):
    """Extended view for single product pages."""
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
```

New concepts here:

- **ViewDTO inheritance** — `ProductDetail` inherits all fields and computed methods from `ProductSummary`, then adds its own. One domain, two views, no duplication.
- **`Field(transform=...)`** — `listed_at` is a `datetime` in the domain but an ISO string in the API. The transform function converts the value at the DTO boundary.
- **Another `@computed`** — `in_stock` is a boolean derived from `stock_kg`.

### Building views from domain objects

```python
# Single product
detail = ProductDetail.from_domain(product)

# List of products
summaries = ProductSummary.from_domains(products)
```

ViewDTOs are frozen — immutable after construction. Data flows one way: domain → view.

## Creating products — BuildDTOs

BuildDTO goes the other direction: external input → domain object.

```python title="application/dtos.py (continued)"
from potato import BuildDTO


class ProductCreate(BuildDTO[Product]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int
```

`id` and `listed_at` are `Auto` fields — Potato automatically excludes them. The user provides the business data; the system provides the rest:

```python
product = dto.to_domain(listed_at=datetime.now(timezone.utc))
# product.id is UNASSIGNED — the database will assign it
# Trying to use product.id before the DB assigns it raises AttributeError
```

No `id=0` placeholder needed. Auto fields default to `UNASSIGNED`, a sentinel that raises on any use (comparison, serialization, casting), making it impossible to accidentally use a placeholder value.

### Partial updates

For PATCH endpoints, use `partial=True` to make all fields optional. Use `exclude=` to prevent certain fields from being changed:

```python title="application/dtos.py (continued)"
class ProductUpdate(BuildDTO[Product], partial=True, exclude=[Product.farmer_id]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    # farmer_id excluded — can't be changed via PATCH
```

Apply only the provided fields to an existing product:

```python
updated_product = update_dto.apply_to(existing_product)
```

`apply_to()` uses Pydantic's `exclude_unset` — only fields the client actually sent are merged. A missing field stays unchanged; a field explicitly set to `null` is different from a field not sent at all.

## The service layer

The service wires DTOs to repositories:

```python title="application/services.py"
class ProductService:
    def __init__(self, product_repo: ProductRepository, farmer_repo: FarmerRepository):
        self.product_repo = product_repo
        self.farmer_repo = farmer_repo

    def list_products(self) -> list[ProductSummary]:
        products = self.product_repo.list_all()
        return ProductSummary.from_domains(products)

    def get_product(self, product_id: int) -> ProductDetail | None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductDetail.from_domain(product)

    def create_product(self, dto: ProductCreate) -> ProductDetail:
        farmer = self.farmer_repo.get_by_id(dto.farmer_id)
        if not farmer:
            raise ValueError(f"Farmer {dto.farmer_id} not found")
        product = dto.to_domain(listed_at=datetime.now(timezone.utc))
        created = self.product_repo.create(product)
        return ProductDetail.from_domain(created)

    def update_product(self, product_id: int, dto: ProductUpdate) -> ProductDetail | None:
        existing = self.product_repo.get_by_id(product_id)
        if not existing:
            return None
        updated = dto.apply_to(existing)
        saved = self.product_repo.update(updated)
        return ProductDetail.from_domain(saved)
```

The pattern is consistent:

- **Read:** repository → domain → `ViewDTO.from_domain()` → API response
- **Create:** API input → `BuildDTO.to_domain()` → domain → repository
- **Update:** API input → `BuildDTO.apply_to(existing)` → domain → repository

## FastAPI routes

```python title="presentation/routers.py"
from fastapi import APIRouter, Depends, HTTPException, status

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.get("", response_model=list[ProductSummary])
def list_products(service: ProductService = Depends(get_product_service)):
    return service.list_products()


@product_router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@product_router.post("", response_model=ProductDetail, status_code=status.HTTP_201_CREATED)
def create_product(dto: ProductCreate, service: ProductService = Depends(get_product_service)):
    try:
        return service.create_product(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@product_router.patch("/{product_id}", response_model=ProductDetail)
def update_product(
    product_id: int,
    dto: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    result = service.update_product(product_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result
```

FastAPI uses the BuildDTO directly as the request body (it's a Pydantic model) and the ViewDTO as the response model. Potato's DTOs are standard Pydantic — they work with FastAPI out of the box.

## Try it

```bash
# List products (seed data)
curl http://localhost:8000/api/products

# Get product detail
curl http://localhost:8000/api/products/1

# Create a new product
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Wild Mushrooms", "price_per_kg": 12.99,
       "description": "Foraged locally.", "stock_kg": 10.0,
       "category": "Specialty", "farmer_id": 1}'

# Update just the price
curl -X PATCH http://localhost:8000/api/products/5 \
  -H "Content-Type: application/json" \
  -d '{"price_per_kg": 14.99}'
```

!!! info "What we built"
    - Product CRUD endpoints (list, detail, create, update, delete)
    - `ProductSummary` and `ProductDetail` ViewDTOs (with inheritance)
    - `ProductCreate` and `ProductUpdate` BuildDTOs (with partial)
    - Service layer connecting DTOs to repositories

    **Potato concepts introduced:** `ViewDTO`, `BuildDTO`, `from_domain()`, `from_domains()`, `to_domain()`, `apply_to()`, `@computed`, `Field(transform=...)`, ViewDTO inheritance, `partial=True`, `exclude=`, `UNASSIGNED`

---

[:material-arrow-left: Previous: Domain & Database](step-01-domain-and-database.md){ .md-button }
[Next: Step 3 — The Farmer API :material-arrow-right:](step-03-farmer-api.md){ .md-button }
