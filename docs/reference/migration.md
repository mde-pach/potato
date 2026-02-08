# Migration Guide

## v1 → v2 Changes

| v1 (Old) | v2 (New) |
|----------|----------|
| `System[T]` | `Auto[T]` |
| Added `Private[T]` | `Private[T]` — never-exposed fields |
| `.build(entity)` | `.from_domain(entity)` |
| `.build_many(entities)` | `.from_domains(entities)` |
| `Aggregate[T1, T2]` (generic) | Field-based `Aggregate` (no generics) |
| `User.alias("buyer")` | `buyer: User` field in Aggregate |
| `Annotated[str, Buyer.username]` | `Field(source=Aggregate.buyer.username)` |
| `View.build(buyer=b, seller=s)` | `View.from_domain(aggregate_instance)` |

## Key Changes

### Auto[T] replaces System[T]

```python
# v1
class User(Domain):
    id: System[int]

# v2
class User(Domain):
    id: Auto[int]
```

### Private[T] is new

```python
# v2 only
class User(Domain):
    password_hash: Private[str]  # Never exposed in any DTO
```

### Field-based Aggregates

```python
# v1
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class Transaction(Aggregate[Buyer, Seller, Product]):
    pass

class TransactionView(ViewDTO[Transaction]):
    buyer_name: Annotated[str, Buyer.username]

view = TransactionView.build(buyer=buyer, seller=seller, product=product)

# v2
class Transaction(Aggregate):
    buyer: User
    seller: User
    product: Product

class TransactionView(ViewDTO[Transaction]):
    buyer_name: str = Field(source=Transaction.buyer.username)

transaction = Transaction(buyer=buyer, seller=seller, product=product)
view = TransactionView.from_domain(transaction)
```

### from_domain() replaces build()

```python
# v1
view = UserView.build(user)
views = UserView.build_many(users)

# v2
view = UserView.from_domain(user)
views = UserView.from_domains(users)
```
