# Step 5: Access Control & Error Messages

The API is functional. Now let's look at two things that make it production-ready: context-dependent field visibility and Potato's class-definition-time error validation.

## Field visibility — `Field(visible=...)`

In Step 3, we added this to `FarmerView`:

```python
email: str = Field(visible=lambda ctx: ctx.is_admin)
```

Let's understand the full mechanism.

### The context object

The context can be any object. We use a simple dataclass:

```python title="application/context.py"
from dataclasses import dataclass

@dataclass
class Permissions:
    is_admin: bool
    user_id: int | None = None
```

### How visibility works

1. Fields with `visible=...` keep their declared type — `email: str` stays `str`, not `str | None`.
2. During `from_domain()`, all fields are populated with their real values. Potato evaluates the visibility predicate against the context.
3. Fields that fail the check are tracked internally as hidden.
4. `model_dump()` and `model_dump_json()` exclude hidden fields entirely — but the value is still accessible on the instance (`view.email` works).

```python
farmer = Farmer(
    id=1, username="green_acres", email="alice@greenacres.farm",
    display_name="Green Acres Farm", password_hash="hashed",
    farm_address=FarmAddress(
        street="123 Farm Road", city="Portland", state="OR", zip_code="97201",
    ),
    joined_at=datetime(2024, 3, 15, tzinfo=timezone.utc),
)

# Admin sees email
admin_view = FarmerView.from_domain(farmer, context=Permissions(is_admin=True))
print(admin_view.model_dump())
# {'id': 1, 'handle': 'green_acres', 'display_name': 'Green Acres Farm',
#  'city': 'Portland', 'state': 'OR', 'email': 'alice@greenacres.farm',
#  'member_since': 'March 2024'}

# Public user doesn't
public_view = FarmerView.from_domain(farmer, context=Permissions(is_admin=False))
print(public_view.model_dump())
# {'id': 1, 'handle': 'green_acres', 'display_name': 'Green Acres Farm',
#  'city': 'Portland', 'state': 'OR', 'member_since': 'March 2024'}
```

The `email` field is completely absent from the public response — not `null`, not empty, just not there.

### No context = hidden by default

```python
view = FarmerView.from_domain(farmer)  # no context
# email is hidden — no context means the predicate can't return True
```

### `visible` vs `Private`

| | `Private[T]` | `Field(visible=...)` |
|---|---|---|
| **Enforcement** | Class definition time | Runtime |
| **Scope** | All ViewDTOs, always | Per-request, based on context |
| **Override** | No escape hatch | Passes when predicate returns `True` |
| **Use case** | Secrets (passwords, tokens) | Sensitive but sometimes needed (email, phone) |

Use `Private` for data that must **never** leave the domain. Use `visible` for data that **some** users can see.

## Error messages

Potato validates DTOs at class definition time. Errors appear when Python loads the class — not when a request hits your endpoint, not in a test. Here are the most common.

### Exposing a Private field

```python
class BadFarmerView(ViewDTO[Farmer]):
    id: int
    username: str
    password_hash: str  # Private field!
```

```
TypeError: In 'BadFarmerView', field 'password_hash' is marked as Private
in 'Farmer' and cannot be exposed in a ViewDTO.

  Hint: Remove 'password_hash' from 'BadFarmerView' or use
  'exclude=[Farmer.password_hash]' to exclude it.
```

### Referencing the wrong domain

```python
class ProductView(ViewDTO[Product]):
    id: int
    farmer_name: str = Field(source=Farmer.display_name)  # Wrong domain!
```

```
TypeError: In 'ProductView', field 'farmer_name' references 'Farmer.display_name',
but 'ProductView' is bound to 'Product'.

  Hint: If you need fields from multiple domains, use an Aggregate:
    class MyAggregate(Aggregate):
        product: Product
        farmer: Farmer
    class ProductView(ViewDTO[MyAggregate]): ...
```

### Referencing a field that doesn't exist

```python
class FarmerView(ViewDTO[Farmer]):
    id: int
    nickname: str = Field(source=Farmer.nickname)
```

```
TypeError: In 'FarmerView', field 'nickname' maps to 'Farmer.nickname'
which does not exist.

  Available fields: ['id', 'username', 'email', 'display_name',
  'password_hash', 'farm_address', 'joined_at']
```

### Domain not in aggregate

```python
class OrderView(ViewDTO[OrderDetail]):
    shipper: str = Field(source=Shipper.name)
```

```
TypeError: In 'OrderView', field 'shipper' references 'Shipper' which is
not in 'OrderDetail'. Allowed domains: Order.

  Hint: 'Shipper' is not a field in 'OrderDetail'. Declare it as a field
  in the Aggregate:
    class OrderDetail(Aggregate):
        shipper: Shipper
```

### Why this matters

Every error includes:

1. **What went wrong** — which field, which DTO, which domain
2. **Why** — the constraint that was violated
3. **How to fix it** — a concrete suggestion with code

These fire at import time, so CI catches them even if the specific endpoint isn't tested. You can't ship a broken DTO.

!!! info "What we covered"
    - `Field(visible=...)` for context-dependent field inclusion
    - `Permissions` context passed through `from_domain()`
    - The difference between `Private` (hard) and `visible` (soft) boundaries
    - Four common error patterns with their messages and fixes

    **Potato concepts introduced:** `Field(visible=...)`, context objects, class-definition-time error validation

---

[:material-arrow-left: Previous: The Order API](step-04-order-api.md){ .md-button }
[Next: Step 6 — The Complete Spud Market :material-arrow-right:](step-06-complete.md){ .md-button }
