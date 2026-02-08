# Non-Domain Fields

BuildDTOs can include fields that don't exist on the domain model. This is useful when the API accepts data that needs transformation before becoming a domain field.

## Extra Fields

A common pattern: accept a `password` field and hash it before creating the domain:

```python
from potato import Domain, BuildDTO, Private

class User(Domain):
    id: int
    username: str
    password_hash: Private[str]

class CreateUser(BuildDTO[User]):
    username: str
    password: str  # Not a domain field — extra field
```

## to_domain() Auto-Filtering

`to_domain()` automatically filters out non-domain fields:

```python
dto = CreateUser(username="alice", password="secret123")

# 'password' is ignored, 'password_hash' must be provided
user = dto.to_domain(id=1, password_hash=hash_password(dto.password))
```

You can access the extra field on the DTO (e.g., `dto.password`) to compute the domain field's value.

## Override Pattern

For field transformations, use `to_domain()` with keyword overrides:

```python
def create_user(dto: CreateUser) -> User:
    return dto.to_domain(
        id=generate_id(),
        password_hash=hash_password(dto.password),
    )
```

The keyword arguments to `to_domain()` are merged with the DTO's domain-compatible fields. Explicit keyword arguments take precedence.

## Next Steps

- **[BuildDTO](../fundamentals/builddto.md)** — BuildDTO basics
- **[Partial Updates](partial-updates.md)** — partial=True and apply_to()
