# Partial Updates

Partial BuildDTOs make all fields optional, enabling PATCH-style updates where only changed fields are sent.

## partial=True

Add `partial=True` to make all fields optional with default `None`:

```python
from potato import Domain, BuildDTO, Auto, Private

class User(Domain):
    id: Auto[int]
    username: str
    email: str
    password_hash: Private[str]
    is_active: bool = True

class UserUpdate(BuildDTO[User], partial=True):
    username: str
    email: str
    is_active: bool
    # All fields become Optional with default None
```

Only set the fields you want to update:

```python
update = UserUpdate(username="new_name")
# update.email is None (not set)
# update.is_active is None (not set)
```

## apply_to()

Apply partial updates to an existing domain instance:

```python
existing = User(id=1, username="alice", email="alice@example.com",
                password_hash="hashed", is_active=True)

update = UserUpdate(username="new_alice")
updated = update.apply_to(existing)

print(updated.username)   # "new_alice" (changed)
print(updated.email)      # "alice@example.com" (unchanged)
print(updated.is_active)  # True (unchanged)
print(updated.id)         # 1 (unchanged)
```

`apply_to()` uses `exclude_unset=True` — only fields explicitly provided in the update are changed. It returns a **new** domain instance (the original is not mutated).

## exclude=[]

Prevent specific fields from being included in a BuildDTO:

```python
class UserUpdate(BuildDTO[User], partial=True, exclude=["is_active"]):
    username: str
    email: str
    # is_active cannot be updated through this DTO
```

## PATCH Endpoint Pattern

A typical partial update endpoint:

```python
from fastapi import APIRouter

router = APIRouter()

class UserUpdate(BuildDTO[User], partial=True):
    username: str
    email: str

@router.patch("/users/{user_id}")
def update_user(user_id: int, dto: UserUpdate) -> UserView:
    existing = fetch_user(user_id)
    updated = dto.apply_to(existing)
    save_user(updated)
    return UserView.from_domain(updated)
```

## Next Steps

- **[BuildDTO](../fundamentals/builddto.md)** — BuildDTO basics
- **[Non-Domain Fields](non-domain-fields.md)** — Extra fields and to_domain() override
