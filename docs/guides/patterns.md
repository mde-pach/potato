# Common Patterns

This guide covers common patterns and best practices when using Potato in real-world applications.

## API Response Pattern

The most common pattern: transform domain models into API responses.

```python
from potato.domain import Domain
from potato.dto import ViewDTO
from typing import Annotated

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

def get_user(user_id: int) -> UserView:
    user = fetch_user_from_database(user_id)
    return UserView.build(user)
```

### With Field Renaming

Rename fields to match API contracts:

```python
class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]  # Rename username → login
    email_address: Annotated[str, User.email]  # Rename email → email_address

def get_user(user_id: int) -> UserView:
    user = fetch_user_from_database(user_id)
    return UserView.build(user)
```

## API Request Pattern

Handle incoming API requests and convert to domain models.

```python
from potato.dto import BuildDTO

class CreateUser(BuildDTO[User]):
    username: str
    email: str

def create_user(create_dto: CreateUser) -> User:
    # Validate and create domain model
    user = User(
        **create_dto.model_dump(),
        id=generate_id(),
        created_at=get_current_timestamp()
    )
    
    # Save to database
    save_user(user)
    
    return user
```

### With Additional Validation

Add server-side validation:

```python
def create_user(create_dto: CreateUser) -> User:
    # Check if username already exists
    if username_exists(create_dto.username):
        raise ValueError("Username already exists")
    
    # Create domain model
    user = User(
        **create_dto.model_dump(),
        id=generate_id(),
        created_at=get_current_timestamp()
    )
    
    save_user(user)
    return user
```

## Update Pattern

Handle partial updates:

```python
class UpdateUser(BuildDTO[User]):
    username: str | None = None
    email: str | None = None

def update_user(user_id: int, update_dto: UpdateUser) -> User:
    user = fetch_user_from_database(user_id)
    
    # Update only provided fields
    update_data = update_dto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    save_user(user)
    return user
```

## Aggregate Composition Pattern

Compose multiple domains into aggregates:

```python
from potato.domain.aggregates import Aggregate
from typing import Annotated

class Order(Domain[Aggregate[User, Product, Price]]):
    customer: User
    product: Product
    price_amount: Annotated[int, Price.amount]
    quantity: int

def create_order(customer_id: int, product_id: int, quantity: int) -> Order:
    customer = fetch_user(customer_id)
    product = fetch_product(product_id)
    price = calculate_price(product, quantity)
    
    order = Order(
        customer=customer,
        product=product,
        price_amount=price.amount,
        quantity=quantity
    )
    
    save_order(order)
    return order
```

## ViewDTO from Aggregates

Create views from multiple domains:

```python
class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    quantity: int

def get_order(order_id: int) -> OrderView:
    order = fetch_order(order_id)
    return OrderView.build(order.customer, order.product)
```

## Transaction Pattern with Aliasing

Handle transactions with multiple parties:

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

def get_transaction(transaction_id: int) -> TransactionView:
    transaction = fetch_transaction(transaction_id)
    return TransactionView.build(
        buyer=transaction.buyer,
        seller=transaction.seller,
        product=transaction.product
    )
```

## Error Handling Pattern

Handle validation errors gracefully:

```python
from pydantic import ValidationError

def handle_create_user(data: dict) -> tuple[User, None] | tuple[None, dict]:
    try:
        create_dto = CreateUser(**data)
        user = User(**create_dto.model_dump(), id=generate_id())
        save_user(user)
        return user, None
    except ValidationError as e:
        errors = {err["loc"][0]: err["msg"] for err in e.errors()}
        return None, errors
```

## List Response Pattern

Handle collections:

```python
def get_users() -> list[UserView]:
    users = fetch_all_users()
    return [UserView.build(user) for user in users]
```

### With Pagination

```python
def get_users(page: int, per_page: int) -> tuple[list[UserView], int]:
    users, total = fetch_users_paginated(page, per_page)
    views = [UserView.build(user) for user in users]
    return views, total
```

## Naming Conventions

### Domain Models

Use singular nouns:

```python
class User(Domain): ...
class Product(Domain): ...
class Order(Domain): ...
```

### BuildDTOs

Use action verbs:

```python
class CreateUser(BuildDTO[User]): ...
class UpdateUser(BuildDTO[User]): ...
class DeleteUser(BuildDTO[User]): ...
```

### ViewDTOs

Use descriptive nouns:

```python
class UserView(ViewDTO[User]): ...
class UserSummary(ViewDTO[User]): ...
class UserDetail(ViewDTO[User]): ...
```

### Aliases

Use descriptive role names:

```python
Buyer = User.alias("buyer")
Seller = User.alias("seller")
Admin = User.alias("admin")
```

## Best Practices

### 1. Keep DTOs Focused

Each DTO should serve a specific purpose:

```python
# ✅ Good: Specific purpose
class UserSummary(ViewDTO[User]):
    id: int
    username: str

class UserDetail(ViewDTO[User]):
    id: int
    username: str
    email: str
    created_at: str

# ❌ Bad: One DTO for everything
class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str
    # Sometimes includes email, sometimes doesn't
```

### 2. Use Type Hints

Always use type hints for better IDE support and type checking:

```python
def create_user(create_dto: CreateUser) -> User:
    ...
```

### 3. Validate Early

Validate data as soon as it enters your system:

```python
def create_user(create_dto: CreateUser) -> User:
    # Validation happens in CreateUser constructor
    # Additional business validation here
    ...
```

### 4. Don't Expose Internal Fields

Only include fields that should be exposed:

```python
# ✅ Good: Only public fields
class UserView(ViewDTO[User]):
    id: int
    username: str

# ❌ Bad: Exposes internal fields
class UserView(ViewDTO[User]):
    id: int
    username: str
    password_hash: str  # Should never be exposed!
```

### 5. Use Field Mapping for API Compatibility

Rename fields to match external API contracts:

```python
class UserView(ViewDTO[User]):
    user_id: Annotated[int, User.id]  # Matches external API
    login: Annotated[str, User.username]  # Matches external API
```

## Common Mistakes

### Mistake 1: Mutating ViewDTOs

```python
# ❌ Wrong: ViewDTOs are immutable
view = UserView.build(user)
view.username = "new_name"  # Raises ValidationError

# ✅ Correct: Create new view if needed
user.username = "new_name"
view = UserView.build(user)
```

### Mistake 2: Wrong Argument Order

```python
# ❌ Wrong: Wrong order
view = OrderView.build(product, user)  # Should be user, product

# ✅ Correct: Match Aggregate order
view = OrderView.build(user, product)
```

### Mistake 3: Forgetting Named Arguments for Aliases

```python
# ❌ Wrong: Positional arguments with aliases
view = TransactionView.build(buyer, seller, product)

# ✅ Correct: Named arguments
view = TransactionView.build(buyer=buyer, seller=seller, product=product)
```

## Next Steps

- **[Examples](examples.md)** - Complete real-world examples
- **[ViewDTO](../core/viewdto.md)** - Learn more about ViewDTO
- **[BuildDTO](../core/builddto.md)** - Learn more about BuildDTO

