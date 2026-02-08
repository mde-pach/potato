# Field Visibility

`Field(visible=...)` controls whether a field appears in serialized output based on a context object. Use it for role-based field exposure.

## Basic Usage

```python
from potato import Domain, ViewDTO, Field

class Permissions:
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User, Permissions]):
    id: int
    username: str
    email: str = Field(visible=lambda ctx: ctx.is_admin)
```

The second type parameter (`Permissions`) declares the context type.

## Passing Context

Provide the context when building the ViewDTO:

```python
user = User(id=1, username="alice", email="alice@example.com")

# Admin sees email
admin_view = UserView.from_domain(user, context=Permissions(is_admin=True))
print(admin_view.model_dump())
# {"id": 1, "username": "alice", "email": "alice@example.com"}

# Non-admin doesn't see email
user_view = UserView.from_domain(user, context=Permissions(is_admin=False))
print(user_view.model_dump())
# {"id": 1, "username": "alice"}
```

## No Context = Hidden

If no context is provided and a field has `visible=...`, the field is excluded:

```python
view = UserView.from_domain(user)  # No context
print(view.model_dump())
# {"id": 1, "username": "alice"}  — email hidden
```

## Serialization-Only Exclusion

Hidden fields are excluded from **serialization only**. The field still exists on the instance with its declared type:

```python
view = UserView.from_domain(user, context=Permissions(is_admin=False))
print(view.email)       # "alice@example.com" — still accessible
print(view.model_dump())  # email excluded from output
```

This means you can use visible fields in `@computed` or `@after_build` even when they're hidden from serialization.

## Context Objects

The context can be any type — a dataclass, Pydantic model, or plain class:

```python
from dataclasses import dataclass

@dataclass
class RequestContext:
    user_role: str
    is_authenticated: bool

class UserView(ViewDTO[User, RequestContext]):
    id: int
    username: str
    email: str = Field(visible=lambda ctx: ctx.user_role == "admin")
    internal_notes: str = Field(visible=lambda ctx: ctx.is_authenticated)
```

## Private vs Visible

| Feature | `Private[T]` | `Field(visible=...)` |
|---------|-------------|---------------------|
| **Scope** | Domain-level marker | ViewDTO field option |
| **Effect** | **Never** in any ViewDTO (TypeError) | Conditional serialization exclusion |
| **When** | Sensitive data (passwords, keys) | Role-based access (admin-only fields) |
| **Enforcement** | Class-definition time | Runtime (per-request context) |

Use `Private[T]` for data that must **never** leave the domain. Use `visible` for data that **some** consumers can see.

## Next Steps

- **[Nested ViewDTOs](nested-viewdtos.md)** — Context propagation through nested builds
- **[Lifecycle Hooks](lifecycle-hooks.md)** — @before_build, @after_build
- **[Domain Models](../fundamentals/domain.md)** — Private[T] field marker
