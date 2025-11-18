# Quickstart Guide

Get started with Potato in minutes. This guide walks you through installing Potato and creating your first domain models and DTOs.

## Installation

Install Potato using pip:

```bash
pip install potato
```

Or with uv:

```bash
uv add potato
```

Or with poetry:

```bash
poetry add potato
```

## Your First Domain Model

Let's start by creating a simple domain model:

```python
from potato.domain import Domain

class User(Domain):
    id: int
    username: str
    email: str
```

That's it! You've created a domain model. Domain models are just Pydantic models with some extra features.

```python
user = User(id=1, username="alice", email="alice@example.com")
print(user.username)  # "alice"
```

## Creating a ViewDTO

A `ViewDTO` transforms your domain model into a format suitable for external consumption (like API responses):

```python
from potato.dto import ViewDTO
from typing import Annotated

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

# Create a view from a domain model
view = UserView.build(user)
print(view.username)  # "alice"
```

### Field Renaming

You can rename fields when creating views:

```python
class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]  # Maps username → login
    email: str

view = UserView.build(user)
print(view.login)  # "alice" (from user.username)
```

The `Annotated[type, Domain.field]` syntax tells Potato to map the DTO field to a specific domain field.

## Creating a BuildDTO

A `BuildDTO` represents data coming from external sources (like API requests):

```python
from potato.dto import BuildDTO

class CreateUser(BuildDTO[User]):
    username: str
    email: str

# Create a DTO from external data
create_dto = CreateUser(username="bob", email="bob@example.com")

# Convert to domain model (you'll typically add generated fields like ID)
user = User(**create_dto.model_dump(), id=2)
print(user.username)  # "bob"
```

## Complete Example

Here's a complete example showing the full data flow:

```python
from potato.domain import Domain
from potato.dto import ViewDTO, BuildDTO
from typing import Annotated

# 1. Define your domain model
class User(Domain):
    id: int
    username: str
    email: str
    created_at: str  # Simplified for example

# 2. Define input DTO (for API requests)
class CreateUser(BuildDTO[User]):
    username: str
    email: str

# 3. Define output DTO (for API responses)
class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]
    email: str
    created_at: str

# 4. Handle incoming request
def create_user(create_dto: CreateUser) -> UserView:
    # Validate and create domain model
    user = User(
        **create_dto.model_dump(),
        id=generate_id(),  # Generated server-side
        created_at=get_current_timestamp()
    )
    
    # Transform to view for response
    return UserView.build(user)

# Usage
create_dto = CreateUser(username="alice", email="alice@example.com")
view = create_user(create_dto)
print(view.login)  # "alice"
```

## Working with Aggregates

Aggregates compose multiple domain models:

```python
from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from typing import Annotated

class Product(Domain):
    id: int
    name: str
    price: int

class Order(Domain[Aggregate[User, Product]]):
    customer: User
    product: Product
    quantity: int

# Create an aggregate
order = Order(
    customer=user,
    product=Product(id=1, name="Widget", price=100),
    quantity=2
)
```

## ViewDTOs from Aggregates

You can create views from multiple domains:

```python
class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_name: Annotated[str, Product.name]
    quantity: int

view = OrderView.build(user, product)
```

## Domain Aliasing

When you need multiple instances of the same domain type:

```python
# Create aliases
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_name: Annotated[str, Buyer.username]
    seller_name: Annotated[str, Seller.username]
    product_name: Annotated[str, Product.name]

# Build with named arguments
view = TransactionView.build(
    buyer=buyer_user,
    seller=seller_user,
    product=product
)
```

## Key Takeaways

1. **Domain models** represent your business entities
2. **BuildDTO** handles incoming data (API requests)
3. **ViewDTO** handles outgoing data (API responses)
4. **Aggregates** compose multiple domains
5. **Aliasing** handles multiple instances of the same domain type

## Next Steps

- **[Domain Models](core/domain.md)** - Deep dive into domain models
- **[ViewDTO](core/viewdto.md)** - Learn about output DTOs
- **[BuildDTO](core/builddto.md)** - Learn about input DTOs
- **[Aggregates](core/aggregates.md)** - Compose multiple domains
- **[Aliasing](core/aliasing.md)** - Handle multiple instances
- **[Examples](guides/examples.md)** - Real-world examples

