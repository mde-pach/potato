# Step 4: The Order API

Orders are the most complex part of Spud Market. An order spans multiple domains (the order itself plus its line items), needs computed totals, and should be validated before being returned. This step brings together aggregates, nested ViewDTOs, and lifecycle hooks.

## Order items — a nested ViewDTO

Each order has line items. Let's create a ViewDTO for a single item:

```python title="application/dtos.py"
from potato import ViewDTO, computed


class OrderItemView(ViewDTO[OrderItem]):
    product_name: str
    quantity_kg: float
    unit_price: float

    @computed
    def line_total(self, item: OrderItem) -> float:
        return round(item.quantity_kg * item.unit_price, 2)
```

`line_total` is computed from two domain fields. It doesn't exist in `OrderItem` — it's derived at view-build time.

## The order aggregate

An order detail needs data from `Order` plus its `list[OrderItem]`. That's an aggregate:

```python title="domain/aggregates.py"
from potato import Aggregate

class OrderDetail(Aggregate):
    order: Order
    items: list[OrderItem]
```

## The order detail view — everything together

```python title="application/dtos.py (continued)"
from potato import ViewDTO, Field, before_build, after_build


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

There's a lot happening here. Let's break it down.

### Aggregate field access

```python
order_id: int = Field(source=OrderDetail.order.id)
customer_name: str = Field(source=OrderDetail.order.customer_name)
```

`OrderDetail.order.id` navigates through the aggregate: first to the `order` field (an `Order`), then to its `id`. This is the same pattern as deep flattening from Step 3, but through an aggregate namespace instead of a nested domain.

### Nested ViewDTOs

```python
items: list[OrderItemView]
```

When Potato sees that `items` is typed as `list[OrderItemView]`, it automatically calls `OrderItemView.from_domain()` on each item. No manual mapping needed — just declare the type, and Potato builds the nested views recursively. Context is passed through automatically.

### Lifecycle hooks

**`@before_build`** runs before the ViewDTO is constructed. It receives the entity and returns a dict that's merged into the ViewDTO data. `@before_build` automatically wraps the method as a classmethod — no need to stack `@classmethod` manually:

```python
@before_build
def enrich(cls, entity: OrderDetail) -> dict:
    return {
        "item_count": len(entity.items),
        "computed_total": round(
            sum(i.quantity_kg * i.unit_price for i in entity.items), 2
        ),
    }
```

This computes `item_count` and `computed_total` from the aggregate's items before the ViewDTO is even constructed. The returned dict provides values for the `item_count` and `computed_total` fields.

**`@after_build`** runs after construction. It receives the finished instance and can validate, log, or raise errors:

```python
@after_build
def validate_total(self) -> None:
    if self.computed_total <= 0:
        raise ValueError(f"Order {self.order_id} has invalid total: {self.computed_total}")
```

If the computed total is zero or negative, `from_domain()` raises a `ValueError`. This catches data integrity issues at the view layer.

### Hook execution order

1. `@before_build` hooks — compute extra data
2. ViewDTO construction — Pydantic model created
3. `@computed` methods — inject derived values
4. `@after_build` hooks — validate the result

## The service

The order service assembles the aggregate from multiple repositories:

```python title="application/services.py"
class OrderService:
    def __init__(self, order_repo, item_repo, product_repo):
        self.order_repo = order_repo
        self.item_repo = item_repo
        self.product_repo = product_repo

    def create_order(self, customer_name, customer_email, items):
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            status="pending", placed_at=datetime.now(timezone.utc),
        )
        created_order = self.order_repo.create(order)

        order_items = []
        for item_data in items:
            product = self.product_repo.get_by_id(item_data["product_id"])
            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")
            oi = OrderItem(
                order_id=created_order.id,
                product_name=product.name,
                quantity_kg=item_data["quantity_kg"],
                unit_price=product.price_per_kg,
            )
            order_items.append(oi)

        created_items = self.item_repo.create_many(order_items)
        agg = OrderDetail(order=created_order, items=created_items)
        return OrderDetailView.from_domain(agg)

    def get_order(self, order_id):
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return None
        items = self.item_repo.get_for_order(order_id)
        agg = OrderDetail(order=order, items=items)
        return OrderDetailView.from_domain(agg)
```

The service builds the aggregate, and `OrderDetailView.from_domain()` handles everything: field extraction, nested ViewDTO building, before/after hooks, computed fields.

## FastAPI routes

```python title="presentation/routers.py"
from pydantic import BaseModel

class OrderItemInput(BaseModel):
    product_id: int
    quantity_kg: float

class OrderCreateInput(BaseModel):
    customer_name: str
    customer_email: str
    items: list[OrderItemInput]

order_router = APIRouter(prefix="/orders", tags=["Orders"])

@order_router.post("", response_model=OrderDetailView, status_code=status.HTTP_201_CREATED)
def create_order(body: OrderCreateInput, service = Depends(get_order_service)):
    try:
        return service.create_order(
            customer_name=body.customer_name,
            customer_email=body.customer_email,
            items=[item.model_dump() for item in body.items],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@order_router.get("/{order_id}", response_model=OrderDetailView)
def get_order(order_id: int, service = Depends(get_order_service)):
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
```

!!! tip
    Order creation uses a plain Pydantic `OrderCreateInput` instead of a `BuildDTO[Order]` because the order items are looked up from products in the service layer. Not everything needs to be a Potato DTO — use the right tool for the job.

## Try it

```bash
# Create an order
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "items": [
      {"product_id": 1, "quantity_kg": 2.0},
      {"product_id": 2, "quantity_kg": 1.5}
    ]
  }'
# {"order_id": 1, "customer_name": "Jane Doe", "customer_email": "jane@example.com",
#  "status": "pending", "item_count": 2, "computed_total": 11.47,
#  "items": [
#    {"product_name": "Honeycrisp Apple", "quantity_kg": 2.0, "unit_price": 3.49, "line_total": 6.98},
#    {"product_name": "Organic Carrots", "quantity_kg": 1.5, "unit_price": 2.99, "line_total": 4.49}
#  ]}

# Get order detail
curl http://localhost:8000/api/orders/1
```

!!! info "What we built"
    - Order creation and detail endpoints
    - `OrderItemView` with `@computed` line totals
    - `OrderDetailView` with nested ViewDTOs, lifecycle hooks, and aggregate field access
    - Service that assembles aggregates from multiple repositories

    **Potato concepts introduced:** `Aggregate`, aggregate field access, nested ViewDTOs (automatic `from_domain()`), `@before_build`, `@after_build`

---

[:material-arrow-left: Previous: The Farmer API](step-03-farmer-api.md){ .md-button }
[Next: Step 5 — Access Control & Errors :material-arrow-right:](step-05-access-control-and-errors.md){ .md-button }
