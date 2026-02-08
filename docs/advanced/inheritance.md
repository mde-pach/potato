# ViewDTO Inheritance

ViewDTOs can inherit from other ViewDTOs to share common fields. This is useful for summary/detail view pairs.

## Basic Inheritance

```python
from potato import Domain, ViewDTO, Auto
from datetime import datetime

class User(Domain):
    id: Auto[int]
    username: str
    email: str
    created_at: Auto[datetime]

class UserSummary(ViewDTO[User]):
    id: int
    username: str

class UserDetail(UserSummary):  # Inherits id, username
    email: str
    created_at: datetime
```

`UserDetail` automatically includes `id` and `username` from `UserSummary`, plus its own `email` and `created_at`.

## Field Override

Child ViewDTOs can override parent fields:

```python
from potato import Field

class UserSummary(ViewDTO[User]):
    id: int
    name: str = Field(source=User.username)

class UserDetail(UserSummary):
    name: str = Field(source=User.username, transform=str.upper)  # Override with transform
    email: str
```

## When to Use Inheritance

**Use inheritance** when views share a common subset:

```python
# Summary for list endpoints
class ProductSummary(ViewDTO[Product]):
    id: int
    name: str
    price: int

# Detail for single-item endpoints
class ProductDetail(ProductSummary):
    description: str
    category: str
    stock: int
```

**Use separate ViewDTOs** when views have different shapes:

```python
# Public profile (different field set, not a subset)
class UserPublicView(ViewDTO[User]):
    username: str

# Admin view (different field set)
class UserAdminView(ViewDTO[User]):
    id: int
    username: str
    email: str
    created_at: datetime
```

## Next Steps

- **[Nested ViewDTOs](nested-viewdtos.md)** — Auto-building nested types
- **[ViewDTO](../fundamentals/viewdto.md)** — ViewDTO basics
