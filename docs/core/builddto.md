# BuildDTO

`BuildDTO` represents data coming from external sources (API requests, form submissions, etc.). Use `BuildDTO` to validate and transform external data into domain models.

## Basic Usage

Create a `BuildDTO` by inheriting from `BuildDTO[Domain]`:

```python
from potato.domain import Domain
from potato.dto import BuildDTO

class User(Domain):
    id: int
    username: str
    email: str

class CreateUser(BuildDTO[User]):
    username: str
    email: str

# Create a DTO from external data
create_dto = CreateUser(username="alice", email="alice@example.com")
print(create_dto.username)  # "alice"
```

## Converting to Domain Models

`BuildDTO` instances can be converted to domain models using `model_dump()`:

```python
# Create DTO from external data (e.g., API request)
create_dto = CreateUser(username="alice", email="alice@example.com")

# Convert to domain model (add server-generated fields)
user = User(
    **create_dto.model_dump(),
    id=generate_id(),  # Generated server-side
    created_at=get_current_timestamp()
)
```

### Partial DTOs

`BuildDTO` can represent a subset of domain fields. This is useful when some fields are generated server-side:

```python
class CreateUser(BuildDTO[User]):
    username: str
    email: str
    # id is excluded - generated server-side
    # created_at is excluded - generated server-side

# External data only includes user-provided fields
create_dto = CreateUser(username="alice", email="alice@example.com")

# Add server-generated fields when creating domain
user = User(
    **create_dto.model_dump(),
    id=1,
    created_at="2025-01-15T10:00:00Z"
)
```

## Validation

`BuildDTO` uses Pydantic's validation system to ensure data integrity:

```python
from pydantic import ValidationError

try:
    # Invalid data
    create_dto = CreateUser(username=123, email="not-an-email")
except ValidationError as e:
    print(e)  # Validation errors
```

### Custom Validators

You can add custom validation logic:

```python
from pydantic import field_validator

class CreateUser(BuildDTO[User]):
    username: str
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('email must contain @')
        return v.lower()  # Normalize email
```

## Type Coercion

Pydantic automatically coerces compatible types:

```python
class CreateUser(BuildDTO[User]):
    username: str
    email: str

# String "123" can be coerced if needed
# (depends on your Pydantic configuration)
```

## Optional Fields

You can include optional fields in `BuildDTO`:

```python
class CreateUser(BuildDTO[User]):
    username: str
    email: str
    age: int | None = None
    tags: list[str] = []

# All fields optional except username and email
create_dto = CreateUser(username="alice", email="alice@example.com")
create_dto_with_age = CreateUser(
    username="bob",
    email="bob@example.com",
    age=25,
    tags=["developer", "python"]
)
```

## Common Patterns

### API Request Handler

```python
def create_user(create_dto: CreateUser) -> User:
    # Validate and create domain model
    user = User(
        **create_dto.model_dump(),
        id=generate_id(),
        created_at=get_current_timestamp()
    )
    
    # Save to database
    save_user(user)
    
    return user
```

### Update DTOs

Create separate DTOs for updates:

```python
class UpdateUser(BuildDTO[User]):
    username: str | None = None
    email: str | None = None

# Partial updates
update_dto = UpdateUser(username="new_username")
# Only update username, leave email unchanged
```

### Nested DTOs

You can create DTOs for nested structures:

```python
class Address(Domain):
    street: str
    city: str
    zip_code: str

class CreateAddress(BuildDTO[Address]):
    street: str
    city: str
    zip_code: str

class User(Domain):
    id: int
    username: str
    address: Address

class CreateUserWithAddress(BuildDTO[User]):
    username: str
    address: CreateAddress
    
    def to_domain(self) -> User:
        return User(
            id=generate_id(),
            username=self.username,
            address=Address(**self.address.model_dump())
        )
```

## Serialization

`BuildDTO` instances can be serialized:

```python
create_dto = CreateUser(username="alice", email="alice@example.com")

# Convert to dictionary
data = create_dto.model_dump()
# {'username': 'alice', 'email': 'alice@example.com'}

# Convert to JSON string
json_str = create_dto.model_dump_json()
# '{"username":"alice","email":"alice@example.com"}'
```

## Error Handling

Handle validation errors appropriately:

```python
from pydantic import ValidationError

def handle_create_user(data: dict) -> User:
    try:
        create_dto = CreateUser(**data)
        return User(**create_dto.model_dump(), id=generate_id())
    except ValidationError as e:
        # Return validation errors to client
        raise HTTPException(status_code=400, detail=e.errors())
```

## Best Practices

1. **Keep DTOs Minimal**: Only include fields that come from external sources
2. **Use Separate DTOs**: Create different DTOs for create vs update operations
3. **Validate Early**: Validate data as soon as it enters your system
4. **Document Required Fields**: Make it clear which fields are required
5. **Handle Errors Gracefully**: Provide clear error messages for validation failures

## BuildDTO vs ViewDTO

| Aspect | BuildDTO | ViewDTO |
|--------|----------|---------|
| **Purpose** | Inbound data (API requests) | Outbound data (API responses) |
| **Mutability** | Mutable (can be modified) | Immutable (frozen) |
| **Field Mapping** | Not needed (1:1 with domain) | Supports field renaming |
| **Use Case** | Creating domain models | Serializing domain models |

## Next Steps

- **[ViewDTO](viewdto.md)** - Create output DTOs
- **[Domain Models](domain.md)** - Learn about domain models
- **[Patterns](../guides/patterns.md)** - Common patterns and best practices

