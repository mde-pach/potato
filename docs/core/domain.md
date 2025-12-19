# Domain Models

Domain models are the core entities of your application. They represent business concepts and contain both data and behavior.

## Creating Domain Models

Domain models in Potato are built on Pydantic's `BaseModel`, so they inherit all of Pydantic's features:

```python
from potato.domain import Domain

class User(Domain):
    id: int
    username: str
    email: str
    age: int | None = None
    friends: list[str] = []
```

### Field Types

Potato supports all standard Python types and Pydantic field types:

```python
from datetime import datetime
from typing import Optional

class Post(Domain):
    id: int
    title: str
    content: str
    published: bool = False
    created_at: datetime
    author_id: Optional[int] = None
    tags: list[str] = []
    metadata: dict[str, str] = {}
```

### Required vs Optional Fields

Fields without default values are required:

```python
class User(Domain):
    id: int  # Required
    username: str  # Required
    email: str | None = None  # Optional
    age: int = 0  # Optional (has default)
```

## Validation

Domain models use Pydantic's validation system:

```python
from pydantic import ValidationError

try:
    user = User(id="not_an_int", username="alice", email="alice@example.com")
except ValidationError as e:
    print(e)  # Validation errors
```

### Custom Validators

You can add custom validators using Pydantic's `field_validator`:

```python
from pydantic import field_validator

class User(Domain):
    id: int
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('email must contain @')
        return v
```

## Serialization

Domain models can be serialized to dictionaries or JSON:

```python
user = User(id=1, username="alice", email="alice@example.com")

# Convert to dictionary
data = user.model_dump()
# {'id': 1, 'username': 'alice', 'email': 'alice@example.com'}

# Convert to JSON string
json_str = user.model_dump_json()
# '{"id":1,"username":"alice","email":"alice@example.com"}'

# Exclude fields
data = user.model_dump(exclude={'email'})
# {'id': 1, 'username': 'alice'}
```

## Domain Model Best Practices

### 1. Keep Domain Models Focused

Domain models should represent business concepts, not technical concerns:

```python
# ✅ Good: Represents a business concept
class Order(Domain):
    id: int
    customer_id: int
    items: list[OrderItem]
    total: int

# ❌ Bad: Mixed with technical concerns
class Order(Domain):
    id: int
    customer_id: int
    items: list[OrderItem]
    total: int
    api_version: str  # Technical detail, not domain concept
    cache_key: str    # Technical detail, not domain concept
```

### 2. Use Rich Types

Prefer domain-specific types over primitives when it makes sense:

```python
from datetime import datetime
from decimal import Decimal

class Order(Domain):
    id: int
    customer_id: int
    created_at: datetime  # Better than str
    total: Decimal        # Better than float for money
    status: OrderStatus  # Enum instead of string
```

### 3. Keep Validation in Domain Models

Business rules and validation belong in domain models:

```python
from pydantic import field_validator, model_validator

class Order(Domain):
    id: int
    items: list[OrderItem]
    total: int
    
    @model_validator(mode='after')
    def validate_total(self):
        calculated_total = sum(item.price for item in self.items)
        if self.total != calculated_total:
            raise ValueError('Total does not match items')
        return self
```

### 4. Avoid External Dependencies

Domain models should be independent of external systems:

```python
# ✅ Good: No external dependencies
class User(Domain):
    id: int
    username: str

# ❌ Bad: Depends on database
class User(Domain):
    id: int
    username: str
    db_session: Session  # Don't do this
```

## When to Use Domain vs Plain Pydantic

Use `Domain` when:

- ✅ You need aggregate support
- ✅ You want to use domain aliasing
- ✅ You're building a DDD-style application
- ✅ You need field references for ViewDTOs

Use plain Pydantic `BaseModel` when:

- ✅ You're building simple data structures
- ✅ You don't need aggregate or aliasing features
- ✅ You're prototyping quickly

## Field Access as Class Attributes

Potato allows accessing fields as class attributes for use in type annotations:

```python
class User(Domain):
    id: int
    username: str

# This is used in ViewDTO field mappings
from typing import Annotated
from potato.dto import ViewDTO

class UserView(ViewDTO[User]):
    login: Annotated[str, User.username]  # User.username is a field reference
```

This feature is primarily used internally by Potato for field mapping. You typically won't need to use it directly.

## System Fields

System fields live alongside your other domain properties but are marked with `System[T]` to signal that the value is produced by your system (auto-generated IDs, timestamps, computed totals, etc.).

At runtime the field still holds whatever `T` would normally hold—`System[str]` is just a normal `str` value—but the `Annotated` metadata lets `BuildDTO` and `ViewDTO` know how to treat it:

- **BuildDTOs** automatically skip `System[...]` fields because they come from the infrastructure rather than user input.
- **ViewDTOs** require those fields so that consumers always see the full domain state, including IDs and timestamps.

Use `System[T]` whenever a field is managed by your code or your infrastructure so that your DTOs keep a clear boundary between user-provided data and system-managed data. For more patterns and best practices, see [System Fields](../philosophy/system-fields.md).

## Next Steps

- **[ViewDTO](viewdto.md)** - Create output DTOs from domain models
- **[BuildDTO](builddto.md)** - Create domain models from input DTOs
- **[Aggregates](aggregates.md)** - Compose multiple domains
