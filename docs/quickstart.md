# Quickstart Guide

Get started with Potato in 5 minutes! This guide will walk you through creating your first Domain model and DTOs.

## Installation

```bash
pip install potato
```

Or with uv:

```bash
uv add potato
```

## Step 1: Create a Domain Model

A Domain model represents your core business entities. Let's create a simple `User` domain:

```python
from potato import Domain, System

class User(Domain):
    id: System[int]  # System-managed field (auto-generated)
    username: str
    email: str
    is_active: bool = True
```

> **What is `System[T]`?**  
> `System[T]` marks fields that are managed by your system (like auto-generated IDs). These fields are **excluded from `BuildDTO`** but **required in `ViewDTO`**.

## Step 2: Create a ViewDTO (Outbound)

`ViewDTO` is for **outbound data** - when you send data to external consumers (API responses, serialization):

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
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.build(user)

print(view.login)  # "alice"
print(view.display_name)  # "@alice"
print(view.model_dump())  # {"id": 1, "login": "alice", "email": "alice@example.com", "display_name": "@alice"}
```

### Key Features

- **Field Mapping**: `login: str = Field(source=User.username)` maps `username` to `login`
- **Computed Fields**: `@computed` decorator for derived values
- **Immutability**: ViewDTOs are frozen - you can't modify them after creation
- **Type Safety**: Mypy validates that all required domain fields are present

## Step 3: Create a BuildDTO (Inbound)

`BuildDTO` is for **inbound data** - when you receive data from external sources (API requests, user input):

```python
from potato import BuildDTO

class UserCreate(BuildDTO[User]):
    username: str
    email: str
    is_active: bool = True
    # 'id' is automatically excluded (System field)

# Usage - Receiving data from API
dto = UserCreate(username="bob", email="bob@example.com")

# Convert to Domain, providing system fields
user = dto.to_domain(id=2)

print(user.id)  # 2
print(user.username)  # "bob"
```

### Key Features

- **System Field Exclusion**: `id` (marked as `System[int]`) is **not** in the DTO
- **to_domain()**: Converts DTO to Domain instance, requiring system fields as arguments
- **Validation**: Pydantic validation ensures data integrity

## Step 4: Field Mapping Styles

Potato supports two styles of field mapping:

### Style 1: `Field(source=...)`

```python
class UserView(ViewDTO[User]):
    login: str = Field(source=User.username)
```

### Style 2: `Annotated`

```python
from typing import Annotated

class UserView(ViewDTO[User]):
    login: Annotated[str, User.username]
```

Both styles are equivalent. Choose what feels more natural for your codebase.

## Step 5: Enable Mypy Plugin (Optional but Recommended)

Potato includes a Mypy plugin that catches errors at compile time:

**mypy.ini:**
```ini
[mypy]
plugins = potato.mypy
```

Now Mypy will validate:
- All required domain fields are present in ViewDTOs
- Field mappings point to existing domain fields
- Aggregates declare all referenced domains

```python
# Mypy will catch this error!
class BadUserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    # Missing 'email' field - Mypy error!
```

## Next Steps

You now know the basics! Here's what to explore next:

- **[Typed Context](core/viewdto.md#typed-context)**: Pass context to computed fields
- **[Aggregates](core/aggregates.md)**: Compose multiple domains
- **[Domain Aliasing](core/aggregates.md#domain-aliasing)**: Handle multiple instances of the same domain
- **[Best Practices](guides/patterns.md)**: Recommended patterns
- **[Complete Examples](guides/examples.md)**: Real-world use cases

---

**Questions?** Check out the [Core Concepts](concepts.md) guide for deeper understanding.
