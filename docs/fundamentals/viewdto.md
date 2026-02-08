# ViewDTO

`ViewDTO` transforms domain models into external representations. Use it for API responses, serialized data, or any outbound data.

## Basic Usage

Create a `ViewDTO` by inheriting from `ViewDTO[Domain]`:

```python
from potato import Domain, ViewDTO

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

user = User(id=1, username="alice", email="alice@example.com")
view = UserView.from_domain(user)
print(view.username)  # "alice"
```

## from_domain() and from_domains()

Build a single ViewDTO or a list:

```python
# Single entity
view = UserView.from_domain(user)

# Batch
views = UserView.from_domains([user1, user2, user3])
```

## Partial Views

Expose only a subset of domain fields:

```python
class UserSummary(ViewDTO[User]):
    id: int
    username: str
    # email excluded
```

## Field Mapping

Rename fields using `Field(source=...)`:

```python
from potato import Field

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    email: str
```

See [Field Mapping](field-mapping.md) for deep access, flattening, and aggregate paths.

## Computed Fields

Add derived fields with `@computed`:

```python
from potato import computed

class UserView(ViewDTO[User]):
    id: int
    username: str

    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"
```

See [Computed Fields](computed-fields.md) for patterns and error handling.

## Immutability

ViewDTOs are **frozen** by default:

```python
view = UserView.from_domain(user)
view.username = "hacker"  # Raises ValidationError
```

## Serialization

ViewDTOs serialize like any Pydantic model:

```python
view.model_dump()       # dict
view.model_dump_json()  # JSON string
```

## Next Steps

- **[Field Mapping](field-mapping.md)** — Renaming, deep access, flattening
- **[Computed Fields](computed-fields.md)** — Derived values
- **[BuildDTO](builddto.md)** — Inbound data
- **[Aggregates](aggregates.md)** — Multi-domain ViewDTOs
