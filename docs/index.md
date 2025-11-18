# Potato

**Type-safe DTOs and Domain models for unidirectional data flow**

Potato is a Python library that enforces clean separation between your domain models and external data representations. Built on Pydantic, it provides type-safe Data Transfer Objects (DTOs) that ensure unidirectional data flow in your applications.

## Key Features

- **Type-safe Domain Models**: Build rich domain models with compile-time validation
- **Unidirectional Data Flow**: Separate `BuildDTO` (inbound) and `ViewDTO` (outbound) for clear boundaries
- **Aggregate Support**: Compose multiple domains into aggregates with compile-time validation
- **Domain Aliasing**: Handle multiple instances of the same domain type in aggregates
- **Immutable Views**: `ViewDTO` instances are frozen by default, preventing accidental mutations
- **Pydantic Integration**: Built on Pydantic v2 for robust validation and serialization

## Quick Example

```python
from potato.domain import Domain
from potato.dto import ViewDTO, BuildDTO
from typing import Annotated

# Define your domain model
class User(Domain):
    id: int
    username: str
    email: str

# Create a DTO for API responses (outbound)
class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]  # Rename field
    email: str

# Create a DTO for API requests (inbound)
class CreateUser(BuildDTO[User]):
    username: str
    email: str

# Usage
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.build(user)  # Creates immutable view
print(view.login)  # "alice"

# Build domain from external data
create_dto = CreateUser(username="bob", email="bob@example.com")
user = User(**create_dto.model_dump(), id=2) # In a real application, you would typically generate the entity and its auto-generated fields (e.g. ID) through a persistence layer
```

## Installation

```bash
pip install potato
```

Or with your favorite package manager:

```bash
uv add potato
# or
poetry add potato
```

## Why Potato?

Modern applications need clear boundaries between:
- **External data** (API requests, database records, user input)
- **Domain logic** (your business models and rules)
- **External representations** (API responses, serialized data)

Potato enforces these boundaries with type-safe DTOs that:
- Prevent accidental coupling between external and internal representations
- Make data transformations explicit and traceable
- Enable compile-time validation of data flow
- Support complex scenarios like aggregates and multiple domain instances

## Documentation Structure

- **[Concepts](concepts.md)** - Learn about DDD, DTOs, and unidirectional data flow
- **[Quickstart](quickstart.md)** - Get up and running in minutes
- **[Core Features](core/domain.md)** - Deep dive into Domain models, ViewDTO, BuildDTO, Aggregates, and Aliasing
- **[Guides](guides/patterns.md)** - Common patterns and best practices
- **[Examples](guides/examples.md)** - Complete real-world examples
- **[API Reference](api-reference.md)** - Auto-generated API documentation

## Next Steps

1. Read about [core concepts](concepts.md) to understand the philosophy
2. Follow the [quickstart guide](quickstart.md) to build your first DTOs
3. Explore [real-world examples](guides/examples.md) for inspiration

---

**Ready to get started?** → [Quickstart Guide](quickstart.md)

