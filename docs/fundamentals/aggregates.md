# Aggregates

Aggregates compose multiple domain models into a single unit. They make relationships between domains explicit and provide namespaces for ViewDTO field mapping.

## Creating Aggregates

Inherit from `Aggregate` and declare domain-typed fields:

```python
from potato import Domain, Aggregate

class User(Domain):
    id: int
    username: str

class Product(Domain):
    id: int
    name: str
    price: int

class Order(Aggregate):
    customer: User
    product: Product
    quantity: int
```

Domain types are **automatically inferred** from field annotations. No generic parameters needed.

## Creating Instances

```python
user = User(id=1, username="alice")
product = Product(id=1, name="Widget", price=100)

order = Order(customer=user, product=product, quantity=2)
print(order.customer.username)  # "alice"
print(order.quantity)           # 2
```

## ViewDTOs from Aggregates

Use `Field(source=Aggregate.field.subfield)` to access nested domain fields:

```python
from potato import ViewDTO, Field

class OrderView(ViewDTO[Order]):
    customer_name: str = Field(source=Order.customer.username)
    product_name: str = Field(source=Order.product.name)
    product_price: int = Field(source=Order.product.price)
    quantity: int  # Auto-mapped from aggregate's own field

view = OrderView.from_domain(order)
print(view.customer_name)  # "alice"
```

### How Field Access Works

- `Order.customer` returns a `DomainFieldAccessor` for the `User` domain
- `Order.customer.username` returns a `FieldProxy` with namespace `"customer"`
- Potato reads `entity.customer.username` when building the ViewDTO

### Auto-Resolution

Aggregate-level fields (non-domain fields) are auto-resolved by name:

```python
class OrderView(ViewDTO[Order]):
    quantity: int  # Auto-maps to Order.quantity (no Field needed)
    customer_name: str = Field(source=Order.customer.username)  # Explicit
```

## Multiple Instances of Same Domain

Use different field names to distinguish:

```python
class Transaction(Aggregate):
    buyer: User
    seller: User
    product: Product
    amount: int

class TransactionView(ViewDTO[Transaction]):
    buyer_name: str = Field(source=Transaction.buyer.username)
    seller_name: str = Field(source=Transaction.seller.username)
    product_name: str = Field(source=Transaction.product.name)
    amount: int
```

Field names (`buyer`, `seller`) serve as natural namespaces — no aliasing needed.

## Aggregates Can Have Their Own Fields

Non-domain fields store aggregate-level data:

```python
class Order(Aggregate):
    customer: User
    product: Product
    quantity: int
    status: str = "pending"
    discount: float = 0.0
```

## Next Steps

- **[Field Mapping](field-mapping.md)** — Deep field access and flattening
- **[ViewDTO](viewdto.md)** — Create views from aggregates
- **[Domain Models](domain.md)** — Define your entities
