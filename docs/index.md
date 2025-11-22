# Potato Documentation

**Type-safe DTOs for clean architecture in Python**

Welcome to the Potato documentation! Potato helps you build maintainable applications by enforcing clean separation between domain models and external data representations.

## What is Potato?

Potato is a Python library built on Pydantic v2 that provides:

- **Type-safe DTOs**: Data Transfer Objects with compile-time validation
- **Unidirectional Data Flow**: Clear boundaries between inbound and outbound data
- **Domain Models**: Rich business entities separate from external representations
- **Mypy Integration**: Compile-time validation through a Mypy plugin

## Quick Example

```python
from potato import Domain, ViewDTO, BuildDTO, Field, System

class User(Domain):
    id: System[int]
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    email: str

class UserCreate(BuildDTO[User]):
    username: str
    email: str

# Outbound - Domain to DTO
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.build(user)

# Inbound - DTO to Domain
dto = UserCreate(username="bob", email="bob@example.com")
user = dto.to_domain(id=2)
```

## Why Potato?

Modern applications need clear boundaries:

| Layer | Responsibility | Potato Concept |
|-------|---------------|----------------|
| External Input | API requests, user input | `BuildDTO` |
| Domain Logic | Business rules, validation | `Domain` |
| External Output | API responses, serialization | `ViewDTO` |

**Benefits:**
- ✅ Prevent coupling between external and internal representations
- ✅ Make data transformations explicit and traceable
- ✅ Catch errors at compile time with Mypy
- ✅ Enforce immutability where needed

## Documentation Structure

### Getting Started

- **[Quickstart Guide](quickstart.md)** - Get up and running in 5 minutes
- **[Core Concepts](concepts.md)** - Understand the philosophy and design

### Core Features

- **[Domain Models](core/domain.md)** - Define your business entities
- **[ViewDTO](core/viewdto.md)** - Outbound data transformation
- **[BuildDTO](core/builddto.md)** - Inbound data validation
- **[Aggregates](core/aggregates.md)** - Multi-domain composition

### Type Safety

- **[Mypy Plugin](mypy.md)** - Compile-time validation and error detection

### Guides

- **[Best Practices](guides/patterns.md)** - Recommended patterns and anti-patterns
- **[Examples](guides/examples.md)** - Complete real-world examples

## Feature Overview

### ViewDTO (Outbound Data)

Transform domain models to external representations:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Field mapping
    
    @computed
    def display_name(self, user: User) -> str:  # Computed fields
        return f"@{user.username}"
```

**Features:**
- Field mapping (`Field(source=...)` or `Annotated`)
- Computed fields with `@computed`decorator
- Typed context injection
- Immutable by default

### BuildDTO (Inbound Data)

Validate and convert external data to domain models:

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    # System fields are automatically excluded

dto = UserCreate(username="alice", email="alice@example.com")
user = dto.to_domain(id=1)  # Provide system fields
```

**Features:**
- Automatic `System[T]` field exclusion
- `to_domain()` conversion
- Pydantic validation

### System Fields

Mark auto-generated or system-managed fields:

```python
class User(Domain):
    id: System[int]  # Excluded from BuildDTO, required in ViewDTO
    created_at: System[datetime]
    username: str
```

### Aggregates

Compose multiple domains:

```python
class OrderAggregate(Aggregate[Order, User, Product]):
    order: Order
    buyer: User
    product: Product
```

## Installation

```bash
pip install potato
```

**Enable Mypy plugin** in `mypy.ini`:

```ini
[mypy]
plugins = potato.mypy
```

## Quick Navigation

**New to Potato?**
1. Start with the [Quickstart Guide](quickstart.md)
2. Read about [Core Concepts](concepts.md)
3. Explore [real-world examples](guides/examples.md)

**Looking for something specific?**
- [Field mapping](core/viewdto.md#field-mapping)
- [Computed fields](core/viewdto.md#computed-fields)
- [System fields](core/domain.md#system-fields)
- [Aggregates](core/aggregates.md)
- [Mypy validation](mypy.md)

---

**Ready to get started?** → [Quickstart Guide](quickstart.md)
