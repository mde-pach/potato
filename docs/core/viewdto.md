# ViewDTO

`ViewDTO` transforms domain models into external representations. Use `ViewDTO` when you need to send data out of your application (API responses, serialized data, etc.).

## Basic Usage

Create a `ViewDTO` by inheriting from `ViewDTO[Domain]`:

```python
from potato.domain import Domain
from potato.dto import ViewDTO

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

# Create a view from a domain model
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.build(user)
print(view.username)  # "alice"
```

## Field Mapping

You can rename fields when creating views using `Annotated[type, Domain.field]`:

```python
from typing import Annotated

class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]  # Maps username → login
    email: str

view = UserView.build(user)
print(view.login)  # "alice" (from user.username)
```

### How Field Mapping Works

The `Annotated[type, Domain.field]` syntax tells Potato:

- The DTO field type (`str`)
- Which domain field to read from (`User.username`)

Potato automatically extracts the value from the specified domain field.

### Partial Views

You can create views with only a subset of domain fields:

```python
class UserSummary(ViewDTO[User]):
    id: int
    username: str
    # email is excluded

view = UserSummary.build(user)
print(view.username)  # "alice"
# view.email would raise AttributeError
```

## Immutability

`ViewDTO` instances are **frozen** (immutable) by default. This prevents accidental mutations:

```python
view = UserView.build(user)
view.username = "hacker"  # ❌ Raises ValidationError
```

This is intentional: views represent read-only data that's been transformed for external consumption.

## Serialization

`ViewDTO` instances can be serialized like any Pydantic model:

```python
view = UserView.build(user)

# Convert to dictionary
data = view.model_dump()
# {'id': 1, 'username': 'alice', 'email': 'alice@example.com'}

# Convert to JSON string
json_str = view.model_dump_json()
# '{"id":1,"username":"alice","email":"alice@example.com"}'

# Exclude fields
data = view.model_dump(exclude={'email'})
```

## ViewDTOs from Multiple Domains

You can create views from multiple domains using `Aggregate`:

```python
from potato.domain.aggregates import Aggregate
from typing import Annotated

class Product(Domain):
    id: int
    name: str
    price: int

class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_name: Annotated[str, Product.name]
    product_price: Annotated[int, Product.price]

# Build from multiple domains
user = User(id=1, username="alice", email="alice@example.com")
product = Product(id=1, name="Widget", price=100)

view = OrderView.build(user, product)
print(view.customer_name)  # "alice"
print(view.product_name)    # "Widget"
```

### Positional Arguments

When using aggregates with unique domain types, pass domains as positional arguments:

```python
view = OrderView.build(user, product)  # Order matters
```

The order should match the order in `Aggregate[User, Product]`.

## ViewDTOs with Aliased Domains

When you have multiple instances of the same domain type, use aliasing:

```python
# Create aliases
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    product_name: Annotated[str, Product.name]

# Build with named arguments
buyer = User(id=1, username="alice", email="alice@example.com")
seller = User(id=2, username="bob", email="bob@example.com")
product = Product(id=1, name="Widget", price=100)

view = TransactionView.build(
    buyer=buyer,
    seller=seller,
    product=product
)
```

### Named Arguments for Aliases

When using aliased domains, you **must** use named arguments:

```python
# ✅ Correct
view = TransactionView.build(buyer=buyer, seller=seller, product=product)

# ❌ Wrong - raises ValueError
view = TransactionView.build(buyer, seller, product)
```

The argument names (`buyer`, `seller`, `product`) must match the alias names or the lowercase domain name.

## Common Patterns

### API Response Pattern

```python
def get_user(user_id: int) -> UserView:
    user = fetch_user_from_database(user_id)
    return UserView.build(user)
```

### Nested Views

You can create views that include nested domain models:

```python
class Order(Aggregate[User, Product]):
    customer: User
    product: Product

class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]

order = Order(customer=user, product=product)
view = OrderView.build(order.customer, order.product)
```

### Computed Fields

You can add computed fields to views:

```python
from pydantic import computed_field

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.username} ({self.email})"
```

## Error Handling

If you try to build a view with missing required fields, Pydantic will raise a `ValidationError`:

```python
from pydantic import ValidationError

try:
    # Missing required field
    incomplete_view = UserView.build(incomplete_user)
except ValidationError as e:
    print(e)
```

## Best Practices

1. **Keep Views Focused**: Each view should serve a specific purpose
1. **Use Field Mapping**: Rename fields to match external API contracts
1. **Exclude Sensitive Data**: Don't include fields that shouldn't be exposed
1. **Document Field Mappings**: Use clear names that indicate the source domain field
1. **Leverage Immutability**: Rely on frozen views to prevent accidental mutations

## Next Steps

- **[BuildDTO](builddto.md)** - Create input DTOs
- **[Aggregates](aggregates.md)** - Work with multiple domains
- **[Aliasing](aliasing.md)** - Handle multiple instances of the same domain
