# Aggregates

Aggregates compose multiple domain models into a single cohesive unit. They help maintain consistency boundaries and make relationships between domains explicit.

## What are Aggregates?

An aggregate is a cluster of domain objects that are treated as a single unit. In Potato, aggregates are domains that compose multiple other domains.

Aggregates help you:

- **Maintain consistency**: Related domains are kept together
- **Make dependencies explicit**: Clear declaration of which domains are involved
- **Enable validation**: Compile-time checking of aggregate relationships

## Basic Aggregates

Create an aggregate by inheriting from `Aggregate[Domain1, Domain2, ...]`:

```python
from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from typing import Annotated

class User(Domain):
    id: int
    username: str

class Product(Domain):
    id: int
    name: str
    price: int

class Order(Aggregate[User, Product]):
    customer: User
    product: Product
    quantity: int
```

The `Aggregate[User, Product]` declaration makes `Order` an aggregate that encapsulates `User` and `Product` domains. This is more aligned with Domain-Driven Design principles where an Aggregate IS a special kind of Domain.

## Creating Aggregates

Create aggregate instances by providing the required domain instances:

```python
user = User(id=1, username="alice", email="alice@example.com")
product = Product(id=1, name="Widget", price=100)

order = Order(
    customer=user,
    product=product,
    quantity=2
)
```

## Field Extraction

You can extract specific fields from aggregated domains using `Annotated[type, Domain.field]`:

```python
class Price(Domain):
    amount: int
    currency: str

class Order(Aggregate[User, Price, Product]):
    customer: User
    price_amount: Annotated[int, Price.amount]  # Extract amount field
    price_currency: Annotated[str, Price.currency]  # Extract currency field
    product: Product

# Create order with extracted fields
price = Price(amount=100, currency="USD")
order = Order(
    customer=user,
    price_amount=price.amount,
    price_currency=price.currency,
    product=product
)
```

### Why Extract Fields?

Field extraction is useful when:

- You want to denormalize data for performance
- You need to store a snapshot of a value at a point in time
- You want to avoid deep nesting in serialization

## Mixing Full Domains and Extracted Fields

You can mix full domain instances with extracted fields:

```python
class Order(Aggregate[User, Price, Product]):
    customer: User  # Full domain instance
    price_amount: Annotated[int, Price.amount]  # Extracted field
    product: Product  # Full domain instance

order = Order(
    customer=user,  # Full User instance
    price_amount=100,  # Just the amount
    product=product  # Full Product instance
)

# Access full domain
print(order.customer.username)  # "alice"

# Access extracted field
print(order.price_amount)  # 100
```

## ViewDTOs from Aggregates

Create views from multiple domains:

```python
from potato.dto import ViewDTO

class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    quantity: int

# Build view from multiple domains
view = OrderView.build(user, product)
```

### Positional Arguments

When building views from aggregates with unique domain types, use positional arguments:

```python
view = OrderView.build(user, product)  # Order matches Aggregate[User, Product]
```

The order of arguments must match the order in `Aggregate[User, Product]`.

## Complex Aggregates

Aggregates can include multiple instances of different domain types:

```python
class Order(Aggregate[User, User, Product, Price]):
    customer: User  # First User instance
    seller: User   # Second User instance
    product: Product
    price_amount: Annotated[int, Price.amount]

order = Order(
    customer=customer_user,
    seller=seller_user,
    product=product,
    price_amount=100
)
```

When you have multiple instances of the **same** domain type, use [aliasing](aliasing.md).

## Best Practices

### 1. Keep Aggregates Focused

Aggregates should represent a cohesive business concept:

```python
# ✅ Good: Order is a cohesive concept
class Order(Aggregate[User, Product, Price]):
    customer: User
    product: Product
    total: Annotated[int, Price.amount]

# ❌ Bad: Unrelated domains mixed together
class RandomAggregate(Aggregate[User, Product, BlogPost, Comment]):
    # Too many unrelated concepts
```

### 2. Use Field Extraction Sparingly

Extract fields only when there's a clear benefit:

```python
# ✅ Good: Extract price for snapshot
class Order(Aggregate[Price]):
    price_amount: Annotated[int, Price.amount]  # Snapshot of price at order time

# ❌ Bad: Extract everything
class Order(Aggregate[User]):
    user_id: Annotated[int, User.id]
    username: Annotated[str, User.username]
    email: Annotated[str, User.email]
    # Just use the full User instance instead
```

### 3. Document Aggregate Relationships

Make it clear why domains are grouped together:

```python
class Order(Aggregate[User, Product, Price]):
    """
    Order aggregate representing a purchase transaction.
    
    Composed of:
    - User: The customer making the purchase
    - Product: The item being purchased
    - Price: The price at the time of purchase (snapshot)
    """
    customer: User
    product: Product
    price_amount: Annotated[int, Price.amount]
```

## Common Patterns

### E-commerce Order

```python
class Order(Aggregate[User, Product, Price]):
    customer: User
    product: Product
    price_amount: Annotated[int, Price.amount]
    price_currency: Annotated[str, Price.currency]
    quantity: int
    created_at: str
```

### Transaction with Multiple Parties

```python
class Transaction(Aggregate[User, User, Product]):
    buyer: User
    seller: User
    product: Product
    amount: int
```

(For multiple instances of the same domain type, see [Aliasing](aliasing.md))

## Next Steps

- **[Aliasing](aliasing.md)** - Handle multiple instances of the same domain type
- **[ViewDTO](viewdto.md)** - Create views from aggregates
- **[Examples](../guides/examples.md)** - Real-world aggregate examples
