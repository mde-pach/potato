# Data Transfer Objects

Data Transfer Objects (DTOs) are simple structures for **transferring data** between layers or across boundaries. They are a fundamental concept in clean architecture.

## What are DTOs?

DTOs are pure data structures that:

- Have **no behavior** (unlike domain models)
- Are **immutable** (for ViewDTOs)
- Serve a **single purpose** (inbound or outbound)

```python
# Domain model - has behavior
class User(Domain):
    id: int
    username: str
    
    def activate(self) -> None:
        self.is_active = True

# DTO - pure data, no behavior
class UserView(ViewDTO[User]):
    id: int
    username: str
    # No methods, just data
```

## Why DTOs?

### Without DTOs

When you expose domain models directly:

- ❌ **Coupling**: API changes force domain changes
- ❌ **Security**: Internal structure exposed to external consumers
- ❌ **Evolution**: Hard to evolve domain independently
- ❌ **Complexity**: Domain models become bloated with serialization concerns

### With DTOs

DTOs provide:

- ✅ **Stability**: API contracts remain stable while domain evolves
- ✅ **Security**: Only expose what's necessary
- ✅ **Flexibility**: Transform data as needed for different consumers
- ✅ **Separation**: Domain logic stays separate from presentation concerns

## DTO Types in Potato

Potato provides two types of DTOs for unidirectional data flow:

### BuildDTO: Inbound Data

**Purpose**: Validate and convert external data into domain models

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    # System fields (like 'id') are excluded

# Receive external data
dto = UserCreate(username="alice", email="alice@example.com")

# Convert to domain
user = dto.to_domain(id=generate_id())
```

**Use cases:**
- API request bodies
- Form submissions
- External data imports
- Database records → Domain objects

### ViewDTO: Outbound Data

**Purpose**: Transform domain models into external representations

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Field mapping
    email: str

# Convert domain to view
view = UserView.build(user)

# Send to external consumer
return view.model_dump()
```

**Use cases:**
- API responses
- UI data
- Report generation
- Domain objects → Database records

## DTO Best Practices

### 1. Keep DTOs Simple

DTOs should be pure data structures:

```python
# ✅ Good: Simple data structure
class UserView(ViewDTO[User]):
    id: int
    username: str

# ❌ Bad: Adding behavior
class UserView(ViewDTO[User]):
    id: int
    username: str
    
    def get_display_name(self) -> str:  # Don't do this
        return f"@{self.username}"
```

### 2. One Purpose Per DTO

Each DTO should serve a single, clear purpose:

```python
# ✅ Good: Clear purpose
class UserCreate(BuildDTO[User]):  # For creating users
    username: str
    email: str

class UserUpdate(BuildDTO[User]):  # For updating users
    username: str | None = None
    email: str | None = None

# ❌ Bad: One DTO for everything
class UserDTO(BuildDTO[User]):  # Too vague
    username: str | None = None
    email: str | None = None
    # Is this for create or update?
```

### 3. Transform, Don't Expose

Use DTOs to transform data, not just expose domain internals:

```python
# ✅ Good: Transformed for consumer
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Renamed for API
    email: str

# ❌ Bad: Just exposing domain
class UserView(ViewDTO[User]):
    id: int
    username: str  # Internal name exposed
    email: str
```

## Next Steps

- Learn about [Unidirectional Data Flow](unidirectional-data-flow.md) - how DTOs enable clean data flow
- Explore [ViewDTO](../core/viewdto.md) - practical guide to outbound DTOs
- Understand [BuildDTO](../core/builddto.md) - practical guide to inbound DTOs

