# Potato Documentation

**Type-safe DTOs for clean architecture in Python**

Potato helps you build maintainable applications by enforcing clean separation between domain models and external data representations. Built on Pydantic v2.

## Quick Example

```python
from potato import Domain, ViewDTO, BuildDTO, Field, Auto, computed

class User(Domain):
    id: Auto[int]
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    email: str

class UserCreate(BuildDTO[User]):
    username: str
    email: str

# Outbound — Domain to DTO
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.from_domain(user)

# Inbound — DTO to Domain
dto = UserCreate(username="bob", email="bob@example.com")
user = dto.to_domain(id=2)
```

## Why Potato?

| Layer | Responsibility | Potato Concept |
|-------|---------------|----------------|
| External Input | API requests, user input | `BuildDTO` |
| Domain Logic | Business rules, validation | `Domain` |
| External Output | API responses, serialization | `ViewDTO` |

- Prevent coupling between external and internal representations
- Make data transformations explicit and traceable
- Catch errors at class-definition time
- Enforce immutability where needed

## Installation

```bash
pip install potato
```

## Documentation

### Getting Started

- **[Installation](getting-started/installation.md)** — Install and configure
- **[Quickstart](getting-started/quickstart.md)** — Get running in 5 minutes
- **[Key Concepts](getting-started/concepts.md)** — Understand the mental model

### Fundamentals

- **[Domain Models](fundamentals/domain.md)** — Auto[T], Private[T], field references
- **[ViewDTO](fundamentals/viewdto.md)** — Outbound data transformation
- **[BuildDTO](fundamentals/builddto.md)** — Inbound data validation
- **[Aggregates](fundamentals/aggregates.md)** — Multi-domain composition
- **[Field Mapping](fundamentals/field-mapping.md)** — Renaming, deep access, flattening
- **[Computed Fields](fundamentals/computed-fields.md)** — Derived values

### Advanced

- **[Inheritance](advanced/inheritance.md)** — ViewDTO inheritance patterns
- **[Nested ViewDTOs](advanced/nested-viewdtos.md)** — Auto-building nested types
- **[Transforms](advanced/transforms.md)** — Type conversion during mapping
- **[Visibility](advanced/visibility.md)** — Context-based field inclusion
- **[Lifecycle Hooks](advanced/lifecycle-hooks.md)** — @before_build, @after_build
- **[Partial Updates](advanced/partial-updates.md)** — PATCH-style updates
- **[Non-Domain Fields](advanced/non-domain-fields.md)** — Extra BuildDTO fields
- **[Error Messages](advanced/error-messages.md)** — Class-definition-time errors

### Tutorial

- **[Spud Market Tutorial](tutorial/index.md)** — Build a complete app step by step

---

**New to Potato?** Start with the [Quickstart](getting-started/quickstart.md).
