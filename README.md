# Potato 🥔

**Type-safe DTOs for clean architecture in Python**

Potato is a Python library that enforces clean separation between your domain models and external data representations. Built on Pydantic v2, it provides type-safe Data Transfer Objects (DTOs) with compile-time validation through an integrated Mypy plugin.

## Features

- 🛡️ **Type Safety**: Compile-time validation with Mypy plugin
- 🔄 **Unidirectional Data Flow**: Separate `ViewDTO` (outbound) and `BuildDTO` (inbound)
- 🎯 **Field Mapping**: Map domain fields to different names using `Field(source=...)`
- 🧮 **Computed Fields**: Add derived fields with `@computed` decorator
- 📦 **System Fields**: Handle auto-generated fields with `System[T]`
- 🔗 **Aggregates**: Compose multiple domains with type-safe aggregates
- 🏗️ **Domain Aliasing**: Handle multiple instances of the same domain type
- ❄️ **Immutability**: ViewDTOs are frozen by default

## Quick Example

```python
from potato import Domain, ViewDTO, BuildDTO, Field, System, computed

# Define your domain model
class User(Domain):
    id: System[int]  # System-managed field
    username: str
    email: str
    is_active: bool

# Create a ViewDTO for API responses (outbound)
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Map username → login
    email: str
    
    @computed
    def display_name(self, user: User) -> str:
        """Computed field"""
        return f"@{user.username}"

# Create a BuildDTO for API requests (inbound)
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    is_active: bool = True
    # 'id' is excluded (System field)

# Usage - Outbound
user = User(id=1, username="alice", email="alice@example.com", is_active=True)
view = UserView.build(user)
print(view.login)  # "alice"
print(view.display_name)  # "@alice"

# Usage - Inbound
dto = UserCreate(username="bob", email="bob@example.com")
user = dto.to_domain(id=2)  # Provide system fields
```

## Installation

```bash
pip install potato
```

Or with uv:

```bash
uv add potato
```

## Type Safety with Mypy

Potato includes a Mypy plugin that validates your DTOs at compile time:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    # Missing 'email' field - Mypy will catch this!
```

**Enable the plugin** in your `mypy.ini`:

```ini
[mypy]
plugins = potato.mypy
```

## Documentation

- **[Quickstart Guide](docs/quickstart.md)** - Get started in 5 minutes
- **[Core Concepts](docs/concepts.md)** - Understand DTOs and Domain models
- **[ViewDTO Guide](docs/core/viewdto.md)** - Outbound data flow
- **[BuildDTO Guide](docs/core/builddto.md)** - Inbound data flow
- **[Aggregates](docs/core/aggregates.md)** - Multi-domain composition
- **[Mypy Plugin](docs/mypy.md)** - Type safety and validation
- **[Examples](docs/guides/examples.md)** - Real-world use cases

## Why Potato?

Modern applications need clear boundaries between:
- **External data** (API requests, database records)
- **Domain logic** (business models and rules)
- **External representations** (API responses, serialized data)

Potato enforces these boundaries with:
- **Type-safe DTOs** that prevent coupling
- **Explicit transformations** that are easy to trace
- **Compile-time validation** that catches errors early
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

**Ready to get started?** → [Quickstart Guide](docs/quickstart.md)
