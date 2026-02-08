# Potato

**Type-safe DTOs for clean architecture in Python**

Potato is a Python library that enforces clean separation between your domain models and external data representations. Built on Pydantic v2, it provides type-safe Data Transfer Objects (DTOs) with class-definition-time validation via metaclasses.

## Features

- **Type Safety**: Class-definition-time validation via metaclasses
- **Unidirectional Data Flow**: Separate `ViewDTO` (outbound) and `BuildDTO` (inbound)
- **Field Mapping**: Map domain fields to different names using `Field(source=...)`
- **Computed Fields**: Add derived fields with `@computed` decorator
- **Auto Fields**: Handle auto-generated fields with `Auto[T]`
- **Private Fields**: Protect sensitive fields with `Private[T]` (never exposed in DTOs)
- **Aggregates**: Compose multiple domains with field-based aggregates
- **Nested ViewDTOs**: Auto-build nested ViewDTO types
- **ViewDTO Inheritance**: Extend ViewDTOs for summary/detail patterns
- **Partial Updates**: `BuildDTO` with `partial=True` and `apply_to()`
- **Field Transforms**: Transform values with `Field(transform=...)`
- **Field Visibility**: Control visibility with `Field(visible=...)`
- **Lifecycle Hooks**: `@before_build` and `@after_build` decorators
- **Immutability**: ViewDTOs are frozen by default

## Quick Example

```python
from potato import Domain, ViewDTO, BuildDTO, Field, Auto, Private, computed

# Define your domain model
class User(Domain):
    id: Auto[int]  # Auto-managed field
    username: str
    email: str
    password_hash: Private[str]  # Never exposed in DTOs

# Create a ViewDTO for API responses (outbound)
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Map username -> login
    email: str

    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"

# Create a BuildDTO for API requests (inbound)
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    # 'id' (Auto) and 'password_hash' (Private) are excluded

# Usage - Outbound
user = User(id=1, username="alice", email="alice@example.com", password_hash="hashed")
view = UserView.from_domain(user)
print(view.login)  # "alice"
print(view.display_name)  # "@alice"

# Usage - Inbound
dto = UserCreate(username="bob", email="bob@example.com")
user = dto.to_domain(id=2, password_hash="hashed_value")  # Provide auto & private fields
```

## Installation

```bash
pip install potato
```

Or with uv:

```bash
uv add potato
```

## Documentation

- **[Quickstart Guide](docs/quickstart.md)** - Get started in 5 minutes
- **[Philosophy](docs/philosophy/index.md)** - Understand the philosophy and design
- **[ViewDTO Guide](docs/core/viewdto.md)** - Outbound data flow
- **[BuildDTO Guide](docs/core/builddto.md)** - Inbound data flow
- **[Aggregates](docs/core/aggregates.md)** - Multi-domain composition
- **[Validation](docs/mypy.md)** - Class-definition-time validation
- **[Examples](docs/guides/examples.md)** - Real-world use cases

## Why Potato?

Modern applications need clear boundaries between:
- **External data** (API requests, database records)
- **Domain logic** (business models and rules)
- **External representations** (API responses, serialized data)

Potato enforces these boundaries with:
- **Type-safe DTOs** that prevent coupling
- **Explicit transformations** that are easy to trace
- **Class-definition-time validation** that catches errors early
- **Immutable views** that prevent accidental mutations

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Type check
uv run mypy src/

# Run all checks
uv run pytest && uv run mypy src/
```

## License

MIT

---

**Ready to get started?** -> [Quickstart Guide](docs/quickstart.md)
