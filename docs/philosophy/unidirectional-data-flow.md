# Unidirectional Data Flow

Potato enforces **unidirectional data flow** to create clear, predictable data transformations throughout your application.

## The Flow Pattern

Data flows in one direction through your system:

```
External World ──BuildDTO──> Domain ──ViewDTO──> External World
    (Input)                   (Logic)              (Output)
```

This pattern ensures:

- **Clear boundaries**: Each layer has a well-defined responsibility
- **Predictable transformations**: Data always flows in the same direction
- **Easy debugging**: You can trace data flow from input to output
- **Type safety**: Each transformation is validated at compile time

## Inbound Flow: BuildDTO → Domain

**Purpose**: Validate and convert external data into domain models

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str
    # System fields (like 'id') are excluded

# 1. Receive external data
dto = UserCreate(username="alice", email="alice@example.com")

# 2. Convert to domain (with system fields)
user = dto.to_domain(id=generate_id())

# 3. Domain is ready for business logic
user.activate()
```

**Characteristics:**
- External data enters through BuildDTOs
- System fields are provided separately
- Domain models are created, not modified
- Validation happens at the boundary

## Outbound Flow: Domain → ViewDTO

**Purpose**: Transform domain models into external representations

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Field mapping
    email: str

# 1. Start with domain model
user = User(id=1, username="alice", email="alice@example.com")

# 2. Transform to view
view = UserView.build(user)

# 3. Send to external consumer
return view.model_dump()  # {"id": 1, "login": "alice", "email": "alice@example.com"}
```

**Characteristics:**
- Domain models are transformed, not exposed directly
- Field mapping allows renaming/transformation
- Views are immutable (frozen by default)
- Multiple views can represent the same domain

## Why Unidirectional?

### Bidirectional Flow Problems

Without unidirectional flow, you often see:

```python
# ❌ Bad: Domain exposed directly
def get_user(user_id: int) -> User:
    user = repository.get(user_id)
    return user  # Domain leaked to API

# ❌ Bad: External data modifies domain
def update_user(user: User, data: dict) -> User:
    user.username = data["username"]  # Direct mutation
    return user
```

**Problems:**
- Domain internals exposed to external consumers
- Hard to evolve domain without breaking API
- No clear transformation boundaries
- Difficult to track data changes

### Unidirectional Flow Benefits

With unidirectional flow:

```python
# ✅ Good: Clear transformation
def get_user(user_id: int) -> UserView:
    user = repository.get(user_id)  # Domain
    return UserView.build(user)     # View

# ✅ Good: Clear creation
def create_user(data: UserCreate) -> UserView:
    user = data.to_domain(id=generate_id())  # BuildDTO → Domain
    repository.save(user)
    return UserView.build(user)              # Domain → ViewDTO
```

**Benefits:**
- Clear transformation points
- Domain stays independent
- API can evolve separately
- Easy to add new views or build sources

## Data Flow in Practice

### API Endpoint Example

```python
@router.post("/users", response_model=UserView)
def create_user(dto: UserCreate) -> UserView:
    # Inbound: BuildDTO → Domain
    user = dto.to_domain(id=generate_id())
    
    # Business logic
    user.activate()
    repository.save(user)
    
    # Outbound: Domain → ViewDTO
    return UserView.build(user)
```

### Multiple Views

The same domain can have multiple views:

```python
class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

class UserPublicView(ViewDTO[User]):
    id: int
    username: str
    # Email excluded for privacy

class UserAdminView(ViewDTO[User]):
    id: int
    username: str
    email: str
    created_at: datetime
    last_login: datetime | None
```

### Multiple Build Sources

Different sources can create the same domain:

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str

class UserImport(BuildDTO[User]):
    username: str
    email: str
    imported_at: datetime  # Extra field for import

# Both create User domain
user1 = UserCreate(...).to_domain(id=1)
user2 = UserImport(...).to_domain(id=2)
```

## Next Steps

- Learn about [Data Transfer Objects](data-transfer-objects.md) - the building blocks of data flow
- Explore [ViewDTO](../core/viewdto.md) - practical guide to outbound flow
- Understand [BuildDTO](../core/builddto.md) - practical guide to inbound flow

