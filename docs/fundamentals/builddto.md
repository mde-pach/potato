# BuildDTO

`BuildDTO` validates external data and converts it into domain models. Use it for API requests, form submissions, or any inbound data.

## Basic Usage

Create a `BuildDTO` by inheriting from `BuildDTO[Domain]`:

```python
from potato import Domain, BuildDTO

class User(Domain):
    id: int
    username: str
    email: str

class CreateUser(BuildDTO[User]):
    username: str
    email: str

dto = CreateUser(username="alice", email="alice@example.com")
```

## to_domain()

Convert a BuildDTO into a domain instance:

```python
dto = CreateUser(username="alice", email="alice@example.com")
user = dto.to_domain(id=1)

print(user.id)        # 1
print(user.username)  # "alice"
```

Provide `Auto[T]` and `Private[T]` fields as keyword arguments — they're automatically excluded from the BuildDTO.

### Auto Field Exclusion

Fields marked with `Auto[T]` or `Private[T]` in the domain are excluded automatically:

```python
from potato import Auto, Private

class User(Domain):
    id: Auto[int]
    username: str
    email: str
    password_hash: Private[str]

class CreateUser(BuildDTO[User]):
    username: str
    email: str
    # 'id' and 'password_hash' are excluded

dto = CreateUser(username="alice", email="alice@example.com")
user = dto.to_domain(id=1, password_hash="hashed_value")
```

## apply_to()

Apply partial updates to an existing domain instance:

```python
class UserUpdate(BuildDTO[User], partial=True):
    username: str
    email: str

existing = User(id=1, username="alice", email="alice@example.com")
update = UserUpdate(username="new_alice")
updated = update.apply_to(existing)

print(updated.username)  # "new_alice"
print(updated.email)     # "alice@example.com" (unchanged)
```

`apply_to()` only updates fields that were explicitly set (`exclude_unset=True`) and returns a new domain instance.

See [Partial Updates](../advanced/partial-updates.md) for the full guide.

## Validation

BuildDTOs use Pydantic's validation:

```python
from pydantic import field_validator

class CreateUser(BuildDTO[User]):
    username: str
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('email must contain @')
        return v.lower()
```

## Common Patterns

### API Request Handler

```python
def create_user(dto: CreateUser) -> User:
    user = dto.to_domain(id=generate_id())
    save_user(user)
    return user
```

### Update Handler

```python
def update_user(user_id: int, dto: UserUpdate) -> User:
    existing = fetch_user(user_id)
    updated = dto.apply_to(existing)
    save_user(updated)
    return updated
```

## BuildDTO vs ViewDTO

| Aspect | BuildDTO | ViewDTO |
|--------|----------|---------|
| **Direction** | Inbound (API requests) | Outbound (API responses) |
| **Mutability** | Mutable | Immutable (frozen) |
| **Field Mapping** | Not needed (1:1 with domain) | Supports renaming |
| **Auto Fields** | Excluded | Included |
| **Private Fields** | Excluded | Forbidden (TypeError) |
| **Partial** | `partial=True` support | N/A |

## Next Steps

- **[Partial Updates](../advanced/partial-updates.md)** — partial=True, exclude=[], apply_to() deep dive
- **[Non-Domain Fields](../advanced/non-domain-fields.md)** — Extra fields and to_domain() override
- **[ViewDTO](viewdto.md)** — Outbound data
