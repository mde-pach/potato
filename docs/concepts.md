# Core Concepts

Understanding the foundational concepts behind Potato will help you build better applications.

## Domain-Driven Design (DDD)

Potato is inspired by Domain-Driven Design principles:

- **Domain Models** represent your core business entities and rules
- **Ubiquitous Language** ensures consistency across your codebase
- **Bounded Contexts** define clear boundaries between different parts of your system

### Domain Models in Potato

A Domain model is a rich business entity that encapsulates:
- **State**: The data that defines the entity
- **Behavior**: Methods that operate on that data
- **Rules**: Invariants that must always be true

```python
from potato import Domain

class User(Domain):
    id: int
    username: str
    email: str
    
    def activate(self) -> None:
        """Domain behavior"""
        self.is_active = True
```

## Data Transfer Objects (DTOs)

DTOs are simple structures for **transferring data** between layers or across boundaries. Unlike domain models, DTOs:
- Have **no behavior** (pure data)
- Are **immutable** (for ViewDTOs)
- Serve a **single purpose** (inbound or outbound)

### Why DTOs?

Without DTOs, you often:
- Expose internal domain structure to external consumers
- Couple your API to your domain model
- Make it hard to evolve your domain independently

With DTOs, you get:
- **Stability**: API changes don't force domain changes
- **Security**: Only expose what's necessary
- **Flexibility**: Transform data as needed

## Unidirectional Data Flow

Potato enforces **unidirectional data flow** with two types of DTOs:

```
External World ──BuildDTO──> Domain ──ViewDTO──> External World
    (Input)                   (Logic)              (Output)
```

### BuildDTO: Inbound Flow

**Purpose**: Validate and convert external data into domain models

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    # System fields (like 'id') are excluded

# Receive external data
dto = UserCreate(username="alice", email="alice@example.com")

# Convert to domain
user = dto.to_domain(id=generate_id())
```

**Use cases:**
- API request bodies
- Form submissions
- External data imports
- Database records → Domain objects

### ViewDTO: Outbound Flow

**Purpose**: Transform domain models into external representations

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    email: str

# Convert domain to view
view = UserView.build(user)

# Send to external consumer
return view.model_dump()
```

**Use cases:**
- API responses
- UI data
- Report generation
- Domain objects → Database records

## Type Safety

Potato provides **compile-time type safety** through:

### 1. Static Typing

All DTOs and Domains use Python type hints:

```python
class User(Domain):
    id: int  # Not str, not None - exactly int
    username: str
```

### 2. Pydantic Validation

Runtime validation ensures data integrity:

```python
dto = UserCreate(username="alice", email="invalid")  # ValidationError!
```

### 3. Mypy Plugin

The Mypy plugin catches errors **before runtime**:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    # Missing 'email' field - Mypy error!
```

## Immutability

ViewDTOs are **frozen by default**:

```python
view = UserView.build(user)
view.id = 999  # Error! ViewDTO is immutable
```

**Why immutability?**
- Prevents accidental mutations
- Makes data flow predictable
- Enables safe sharing across boundaries
- Easier to reason about

## Aggregates

An **Aggregate** is a cluster of related domain objects treated as a single unit:

```python
from potato import Aggregate

class OrderAggregate(Aggregate[Order, User, Product]):
    order: Order
    buyer: User
    product: Product
```

**Key concepts:**
- **Consistency Boundary**: All changes within an aggregate are atomic
- **Root Entity**: One entity (usually `Order`) is the entry point
- **Encapsulation**: Internal relationships are hidden from outside

### Multi-Domain DTOs

Build DTOs from aggregates:

```python
class OrderView(ViewDTO[OrderAggregate]):
    order_id: int = Field(source=OrderAggregate.order.id)
    buyer_name: str = Field(source=OrderAggregate.buyer.username)
    product_name: str = Field(source=OrderAggregate.product.name)

view = OrderView.build(order_agg)
```

## System Fields

`System[T]` marks fields managed by your system:

```python
class User(Domain):
    id: System[int]  # Auto-generated
    created_at: System[datetime]  # Set by database
    username: str  # User-provided
```

**Behavior:**
- **Excluded from BuildDTO**: Users can't set these fields
- **Required in ViewDTO**: Always present in output
- **Provided to `to_domain()`**: You supply them when creating domains

## Separation of Concerns

Potato enforces clean architecture:

| Layer | Responsibility | Potato Type |
|-------|---------------|-------------|
| **Presentation** | API contracts, serialization | `ViewDTO`, `BuildDTO` |
| **Domain** | Business logic, rules | `Domain` |
| **Infrastructure** | Database, external services | N/A |

**Benefits:**
- Domain logic is **portable** (no dependency on frameworks)
- API can **evolve independently** from domain
- Testing is **easier** (mock DTOs, test domain in isolation)

## Summary

| Concept | Purpose | Potato Implementation |
|---------|---------|----------------------|
| Domain Model | Business entity | `Domain` |
| Inbound DTO | External → Domain | `BuildDTO` |
| Outbound DTO | Domain → External | `ViewDTO` |
| Multi-Domain | Grouped entities | `Aggregate` |
| System Fields | Auto-generated data | `System[T]` |
| Type Safety | Compile-time validation | Mypy plugin |

---

**Next:** Learn how to use these concepts in practice with [ViewDTO](core/viewdto.md) and [BuildDTO](core/builddto.md).
