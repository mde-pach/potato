# Error Messages

Potato validates DTO and Aggregate definitions at class-definition time — errors are raised the moment your class is defined (at import time), before any application code runs. Each error includes a hint on how to fix it.

## Private Field Exposure

```python
class User(Domain):
    id: int
    username: str
    password_hash: Private[str]

class UserView(ViewDTO[User]):
    id: int
    username: str
    password_hash: str
```

**Error:**
```
TypeError: ViewDTO 'UserView' includes Private field 'password_hash'.
Private fields cannot be exposed in ViewDTOs.
```

**Fix:** Remove the private field from the ViewDTO.

## Wrong Domain Reference

```python
class Order(Domain):
    id: int

class UserView(ViewDTO[User]):
    id: int
    order_id: int = Field(source=Order.id)
```

**Error:**
```
TypeError: In 'UserView', field 'order_id' references Order.id,
but ViewDTO is bound to User.

Hint: If you need fields from multiple domains, use an Aggregate.
```

**Fix:** Use an Aggregate to combine User and Order, or remove the cross-domain reference.

## Missing Domain Field

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.unknown_field)
```

**Error:**
```
AttributeError: Domain 'User' has no field 'unknown_field'
```

**Fix:** Check the domain model for the correct field name.

## Domain Not in Aggregate

```python
class OrderAggregate(Aggregate):
    customer: User
    product: Product

class OrderView(ViewDTO[OrderAggregate]):
    shipper_name: str = Field(source=OrderAggregate.shipper.name)
```

**Error:**
```
AttributeError: Aggregate 'OrderAggregate' has no field 'shipper'
```

**Fix:** Add the missing domain to the aggregate, or correct the field name.

## Deep Path Typo

```python
class UserView(ViewDTO[User]):
    city: str = Field(source=User.address.cty)  # Typo: 'cty' instead of 'city'
```

**Error:**
```
AttributeError: Domain 'Address' has no field 'cty'
```

**Fix:** Correct the field name in the path. Potato validates every segment of the path.

## Common Mistakes

### Mutating a ViewDTO

```python
view = UserView.from_domain(user)
view.username = "new_name"  # Raises ValidationError — ViewDTOs are frozen
```

**Fix:** Modify the domain model and create a new ViewDTO.

### Including Auto Fields in BuildDTO

```python
class CreateUser(BuildDTO[User]):
    id: int  # This field is Auto[int] in the domain
    username: str
```

Auto and Private fields are automatically excluded. If you declare them explicitly, they'll be treated as regular BuildDTO fields — provide them via `to_domain()` keyword arguments instead.

## Next Steps

- **[ViewDTO](../fundamentals/viewdto.md)** — ViewDTO basics
- **[BuildDTO](../fundamentals/builddto.md)** — BuildDTO basics
- **[Domain Models](../fundamentals/domain.md)** — Auto[T] and Private[T]
