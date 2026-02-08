# Field Transforms

`Field(transform=...)` applies a function to a field value during ViewDTO construction. Use it for type conversions and formatting.

## Basic Usage

```python
from potato import Domain, ViewDTO, Field
from datetime import datetime

class User(Domain):
    id: int
    username: str
    created_at: datetime

class UserView(ViewDTO[User]):
    id: int
    username: str
    created_at: str = Field(source=User.created_at, transform=lambda dt: dt.isoformat())
```

The transform function receives the raw field value and returns the transformed value.

## Common Transforms

### datetime to ISO string

```python
created_at: str = Field(source=User.created_at, transform=lambda dt: dt.isoformat())
```

### Enum to value

```python
status: str = Field(source=Order.status, transform=lambda s: s.value)
```

### String formatting

```python
username: str = Field(source=User.username, transform=str.upper)
```

### Custom conversion

```python
price_display: str = Field(
    source=Product.price,
    transform=lambda cents: f"${cents / 100:.2f}"
)
```

## Transform with Source

`transform` is often combined with `source` for renaming + conversion:

```python
class ProductView(ViewDTO[Product]):
    name: str
    display_price: str = Field(
        source=Product.price,
        transform=lambda cents: f"${cents / 100:.2f}"
    )
```

## Transform vs @computed

| Feature | `Field(transform=...)` | `@computed` |
|---------|----------------------|-------------|
| **Input** | Single field value | Full domain instance |
| **Best for** | Type conversion, formatting | Deriving new data from multiple fields |
| **Declaration** | Field parameter | Decorated method |

**Use transform** when you're converting a single field:
```python
created_at: str = Field(source=User.created_at, transform=lambda dt: dt.isoformat())
```

**Use @computed** when you need multiple fields:
```python
@computed
def full_name(self, user: User) -> str:
    return f"{user.first_name} {user.last_name}"
```

## Next Steps

- **[Computed Fields](../fundamentals/computed-fields.md)** — Derived fields from domain instance
- **[Field Mapping](../fundamentals/field-mapping.md)** — Renaming and deep access
- **[Visibility](visibility.md)** — Context-based field inclusion
