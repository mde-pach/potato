# Field Mapping

`Field(source=...)` maps domain fields to ViewDTO fields with different names or from nested structures. Potato validates all mappings at class-definition time.

## Renaming Fields

Map a domain field to a differently-named ViewDTO field:

```python
from potato import Domain, ViewDTO, Field

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)           # username → login
    email_address: str = Field(source=User.email)      # email → email_address
```

## Deep Field Access

Access fields from nested domain models:

```python
class Address(Domain):
    city: str
    street: str
    zip_code: str

class User(Domain):
    name: str
    address: Address

class UserView(ViewDTO[User]):
    name: str
    city: str = Field(source=User.address.city)       # Flattens nested field
    street: str = Field(source=User.address.street)
```

This works to any depth — `User.address.city` tells Potato to read `entity.address.city` when building the ViewDTO.

## Aggregate Field Paths

For aggregates, the field name serves as the namespace:

```python
from potato import Aggregate

class Order(Aggregate):
    customer: User
    product: Product
    quantity: int

class OrderView(ViewDTO[Order]):
    customer_name: str = Field(source=Order.customer.username)
    product_name: str = Field(source=Order.product.name)
    quantity: int  # Auto-mapped (no Field needed)
```

Combine with deep access for nested structures within aggregates:

```python
class OrderView(ViewDTO[Order]):
    customer_city: str = Field(source=Order.customer.address.city)
```

## Path Validation

Potato validates field paths at class-definition time. Invalid paths raise errors immediately:

```python
class UserView(ViewDTO[User]):
    login: str = Field(source=User.unknown_field)
    # AttributeError: Domain 'User' has no field 'unknown_field'

class UserView(ViewDTO[User]):
    order_id: int = Field(source=Order.id)
    # TypeError: In 'UserView', field 'order_id' references Order.id,
    # but ViewDTO is bound to User.
    #
    # Hint: If you need fields from multiple domains, use an Aggregate.
```

## Auto-Mapping

Fields that share the same name as a domain field don't need `Field(source=...)`:

```python
class UserView(ViewDTO[User]):
    id: int        # Auto-mapped to User.id
    username: str  # Auto-mapped to User.username
    login: str = Field(source=User.username)  # Explicit mapping needed (different name)
```

## Next Steps

- **[Computed Fields](computed-fields.md)** — Add derived values
- **[Transforms](../advanced/transforms.md)** — Convert types during mapping
- **[Aggregates](aggregates.md)** — Multi-domain composition
