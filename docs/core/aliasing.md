# Domain Aliasing

Domain aliasing allows you to use multiple instances of the same domain type in aggregates and ViewDTOs. This is essential when you need to distinguish between different roles or contexts.

## Why Aliasing?

Consider an e-commerce transaction: you have a buyer and a seller, both of which are `User` instances. Without aliasing, you can't distinguish between them:

```python
# ❌ This doesn't work - can't have two User types
class Transaction(Domain[Aggregate[User, User, Product]]):
    # Which User is which?
```

With aliasing, you can create distinct types:

```python
# ✅ This works - aliases create distinct types
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class Transaction(Domain[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    seller_id: Annotated[int, Seller.id]
    product: Product
```

## Creating Aliases

Create aliases using `Domain.alias("name")`:

```python
from potato.domain import Domain

class User(Domain):
    id: int
    username: str
    email: str

# Create aliases
Buyer = User.alias("buyer")
Seller = User.alias("seller")
Admin = User.alias("admin")
```

Aliases are types that behave like the original domain but with distinct identity for type checking and field references.

## Using Aliases in Aggregates

Use aliases in aggregate declarations:

```python
class Transaction(Domain[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    product: Product
```

### Creating Aggregate Instances

When creating aggregate instances with aliased domains, provide the extracted values:

```python
buyer = User(id=1, username="alice", email="alice@example.com")
seller = User(id=2, username="bob", email="bob@example.com")
product = Product(id=1, name="Widget", price=100)

transaction = Transaction(
    buyer_id=buyer.id,
    buyer_name=buyer.username,
    seller_id=seller.id,
    seller_name=seller.username,
    product=product
)
```

## Using Aliases in ViewDTOs

Create ViewDTOs that reference aliased domains:

```python
from potato.dto import ViewDTO
from typing import Annotated

class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    buyer_email: Annotated[str, Buyer.email]
    
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
```

### Building Views with Named Arguments

When building views with aliased domains, you **must** use named arguments:

```python
buyer = User(id=1, username="alice", email="alice@example.com")
seller = User(id=2, username="bob", email="bob@example.com")
product = Product(id=1, name="Widget", price=100)

# ✅ Correct: Use named arguments
view = TransactionView.build(
    buyer=buyer,
    seller=seller,
    product=product
)

# ❌ Wrong: Positional arguments don't work with aliases
view = TransactionView.build(buyer, seller, product)  # Raises ValueError
```

### Argument Names

The argument names must match:
1. The alias name (if the alias was created with `.alias("name")`)
2. Or the lowercase domain name (for non-aliased domains)

```python
# Aliases
Buyer = User.alias("buyer")  # Use "buyer" as argument name
Seller = User.alias("seller")  # Use "seller" as argument name

# Non-aliased domain
Product  # Use "product" (lowercase domain name)

view = TransactionView.build(
    buyer=buyer_user,    # Matches Buyer alias
    seller=seller_user,  # Matches Seller alias
    product=product      # Matches Product domain name
)
```

## Field References with Aliases

Reference fields from aliased domains using the alias:

```python
class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    # Reference Buyer fields
    buyer_id: Annotated[int, Buyer.id]
    buyer_username: Annotated[str, Buyer.username]
    
    # Reference Seller fields
    seller_id: Annotated[int, Seller.id]
    seller_username: Annotated[str, Seller.username]
    
    # Reference Product fields (not aliased)
    product_name: Annotated[str, Product.name]
```

## Complete Example

Here's a complete example of aliasing in action:

```python
from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from potato.dto import ViewDTO
from typing import Annotated

# Domain model
class User(Domain):
    id: int
    username: str
    email: str

class Product(Domain):
    id: int
    name: str
    price: int

# Create aliases
Buyer = User.alias("buyer")
Seller = User.alias("seller")

# Aggregate with aliased domains
class Transaction(Domain[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    product: Product
    amount: int

# ViewDTO with aliased domains
class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    amount: int

# Usage
buyer = User(id=1, username="alice", email="alice@example.com")
seller = User(id=2, username="bob", email="bob@example.com")
product = Product(id=1, name="Widget", price=100)

# Create transaction
transaction = Transaction(
    buyer_id=buyer.id,
    buyer_name=buyer.username,
    seller_id=seller.id,
    seller_name=seller.username,
    product=product,
    amount=100
)

# Create view
view = TransactionView.build(
    buyer=buyer,
    seller=seller,
    product=product
)

print(view.buyer_name)  # "alice"
print(view.seller_name)  # "bob"
```

## Multiple Aliases

You can create as many aliases as you need:

```python
# Different roles
Buyer = User.alias("buyer")
Seller = User.alias("seller")
Admin = User.alias("admin")
Moderator = User.alias("moderator")

# Different contexts
SourceUser = User.alias("source")
TargetUser = User.alias("target")

# Use in aggregates
class ComplexTransaction(Domain[Aggregate[Buyer, Seller, Admin, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    seller_id: Annotated[int, Seller.id]
    approved_by: Annotated[int, Admin.id]
    product: Product
```

## Best Practices

### 1. Use Descriptive Alias Names

Choose alias names that clearly indicate the role or context:

```python
# ✅ Good: Clear role
Buyer = User.alias("buyer")
Seller = User.alias("seller")

# ❌ Bad: Unclear
User1 = User.alias("user1")
User2 = User.alias("user2")
```

### 2. Keep Aliases Close to Usage

Define aliases near where they're used:

```python
# In transaction.py
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class Transaction(Domain[Aggregate[Buyer, Seller, Product]]):
    ...
```

### 3. Document Alias Purpose

Add comments explaining why aliases are needed:

```python
# Transaction involves two User instances with different roles
Buyer = User.alias("buyer")   # The user making the purchase
Seller = User.alias("seller") # The user selling the product
```

## Common Patterns

### E-commerce Transactions

```python
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class OrderView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    seller_id: Annotated[int, Seller.id]
    product_name: Annotated[str, Product.name]
```

### Social Networks

```python
Follower = User.alias("follower")
Followee = User.alias("followee")

class FollowView(ViewDTO[Aggregate[Follower, Followee]]):
    follower_id: Annotated[int, Follower.id]
    followee_id: Annotated[int, Followee.id]
```

### Relationships

```python
Source = User.alias("source")
Target = User.alias("target")

class RelationshipView(ViewDTO[Aggregate[Source, Target]]):
    source_id: Annotated[int, Source.id]
    target_id: Annotated[int, Target.id]
```

## Next Steps

- **[Aggregates](aggregates.md)** - Learn about aggregates
- **[ViewDTO](viewdto.md)** - Create views with aliases
- **[Examples](../guides/examples.md)** - Real-world aliasing examples

