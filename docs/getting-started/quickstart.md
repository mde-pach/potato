# Quickstart

Get started with Potato in 5 minutes.

## Step 1: Create a Domain Model

A Domain model represents your core business entity:

```python
from potato import Domain, Auto, Private

class User(Domain):
    id: Auto[int]               # System-managed (excluded from BuildDTO)
    username: str
    email: str
    password_hash: Private[str] # Never exposed in any DTO
    is_active: bool = True
```

`Auto[T]` and `Private[T]` control how fields flow through DTOs. See [Domain Models](../fundamentals/domain.md) for details.

## Step 2: Create a ViewDTO (Outbound)

`ViewDTO` transforms domain models into external representations:

```python
from potato import ViewDTO, Field, computed

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Rename field
    email: str

    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"

# Usage
user = User(id=1, username="alice", email="alice@example.com", password_hash="hashed")
view = UserView.from_domain(user)

print(view.login)         # "alice"
print(view.display_name)  # "@alice"
print(view.model_dump())
# {"id": 1, "login": "alice", "email": "alice@example.com", "display_name": "@alice"}
```

## Step 3: Create a BuildDTO (Inbound)

`BuildDTO` validates and converts external data into domain models:

```python
from potato import BuildDTO

class UserCreate(BuildDTO[User]):
    username: str
    email: str
    is_active: bool = True
    # 'id' excluded (Auto), 'password_hash' excluded (Private)

dto = UserCreate(username="bob", email="bob@example.com")
user = dto.to_domain(id=2, password_hash="hashed_value")
```

### Partial Updates

Use `partial=True` to make all fields optional:

```python
class UserUpdate(BuildDTO[User], partial=True):
    username: str
    email: str

update = UserUpdate(username="new_name")
updated_user = update.apply_to(existing_user)
# Only 'username' is updated, other fields stay the same
```

## Step 4: Aggregates

Compose multiple domains with field-based aggregates:

```python
from potato import Aggregate

class Product(Domain):
    id: Auto[int]
    name: str
    price: int

class OrderAggregate(Aggregate):
    customer: User
    product: Product
    quantity: int

class OrderView(ViewDTO[OrderAggregate]):
    customer_name: str = Field(source=OrderAggregate.customer.username)
    product_name: str = Field(source=OrderAggregate.product.name)
    product_price: int = Field(source=OrderAggregate.product.price)
    quantity: int

aggregate = OrderAggregate(customer=user, product=product, quantity=2)
view = OrderView.from_domain(aggregate)
```

## Next Steps

- **[Key Concepts](concepts.md)** — Understand the mental model
- **[Domain Models](../fundamentals/domain.md)** — Auto[T], Private[T], UNASSIGNED
- **[ViewDTO](../fundamentals/viewdto.md)** — Field mapping, computed fields, immutability
- **[BuildDTO](../fundamentals/builddto.md)** — to_domain(), apply_to(), partial updates
- **[Tutorial](../tutorial/index.md)** — Build a complete app step by step
