# Computed Fields

The `@computed` decorator adds derived fields to ViewDTOs. Computed fields receive the domain instance and return a calculated value.

## Basic Usage

```python
from potato import Domain, ViewDTO, computed

class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str

    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"

    @computed
    def email_domain(self, user: User) -> str:
        return user.email.split("@")[1]

view = UserView.from_domain(user)
print(view.display_name)   # "@alice"
print(view.email_domain)   # "example.com"
```

## Signature

A computed field method receives `self` and the domain instance:

```python
@computed
def field_name(self, entity: DomainType) -> ReturnType:
    return ...
```

The return type annotation becomes the field's type in the ViewDTO.

## Patterns

### Formatting

```python
@computed
def formatted_price(self, product: Product) -> str:
    return f"${product.price / 100:.2f}"
```

### Derived Booleans

```python
@computed
def is_premium(self, user: User) -> bool:
    return user.subscription_tier in ("gold", "platinum")
```

### Aggregations

```python
@computed
def item_count(self, order: Order) -> int:
    return len(order.items)
```

## Error Propagation

Errors in computed fields propagate — they are **not** silently swallowed:

```python
@computed
def risky_field(self, user: User) -> str:
    return user.email.split("@")[1]  # Raises IndexError if no '@'
```

If the computation raises an exception, it bubbles up from `from_domain()`.

## Computed vs Transform

| Feature | `@computed` | `Field(transform=...)` |
|---------|-------------|----------------------|
| **Input** | Full domain instance | Single field value |
| **Use case** | Derive new data from multiple fields | Convert a single field's type |
| **Declaration** | Method with decorator | Field parameter |

See [Transforms](../advanced/transforms.md) for `Field(transform=...)`.

## Next Steps

- **[Transforms](../advanced/transforms.md)** — Convert single field values
- **[ViewDTO](viewdto.md)** — ViewDTO basics
- **[Lifecycle Hooks](../advanced/lifecycle-hooks.md)** — @before_build, @after_build
