# Separation of Concerns

Potato enforces clean architecture through clear separation of concerns. Each layer has a well-defined responsibility, making your codebase maintainable and testable.

## The Layered Architecture

Potato follows a layered architecture pattern:

| Layer | Responsibility | Potato Type |
|-------|---------------|-------------|
| **Presentation** | API contracts, serialization | `ViewDTO`, `BuildDTO` |
| **Domain** | Business logic, rules | `Domain` |
| **Infrastructure** | Database, external services | N/A |

## Layer Responsibilities

### Presentation Layer

The presentation layer handles communication with external systems:

**Responsibilities:**
- Define API contracts (request/response shapes)
- Serialize/deserialize data
- Handle HTTP concerns (status codes, headers)
- Validate external input

**Potato Types:**
- `ViewDTO`: Transform domain → external representation
- `BuildDTO`: Transform external data → domain

```python
# Presentation layer
@router.post("/users", response_model=UserView)
def create_user(dto: UserCreate) -> UserView:
    # Convert external data to domain
    user = dto.to_domain(id=generate_id())
    
    # Delegate to domain layer
    user_service.create(user)
    
    # Convert domain to external representation
    return UserView.build(user)
```

### Domain Layer

The domain layer contains your business logic:

**Responsibilities:**
- Define business entities
- Enforce business rules
- Implement business behavior
- Maintain invariants

**Potato Types:**
- `Domain`: Business entities with behavior
- `Aggregate`: Composed business concepts

```python
# Domain layer
class User(Domain):
    id: System[int]
    username: str
    email: str
    is_active: bool = False
    
    def activate(self) -> None:
        """Business logic lives here"""
        if not self.email:
            raise ValueError("Cannot activate user without email")
        self.is_active = True
```

### Infrastructure Layer

The infrastructure layer handles technical concerns:

**Responsibilities:**
- Database access
- External API calls
- File system operations
- Caching

**Potato Types:**
- None (Potato doesn't provide infrastructure types)

```python
# Infrastructure layer
class UserRepository:
    def save(self, user: User) -> None:
        # Database operations
        db.session.add(user)
        db.session.commit()
```

## Benefits of Separation

### Domain Logic is Portable

Domain models have no dependencies on frameworks:

```python
# Domain layer - no framework dependencies
class User(Domain):
    id: System[int]
    username: str
    
    def activate(self) -> None:
        self.is_active = True

# Can be used with any framework
# - FastAPI
# - Django
# - Flask
# - CLI tools
```

### API Can Evolve Independently

API contracts can change without affecting domain:

```python
# Old API
class UserView(ViewDTO[User]):
    id: int
    username: str

# New API - domain unchanged
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Renamed field
    # Domain model unchanged!
```

### Testing is Easier

Each layer can be tested in isolation:

```python
# Test domain logic without API
def test_user_activation():
    user = User(id=1, username="alice", email="alice@example.com")
    user.activate()
    assert user.is_active is True

# Test API without domain
def test_user_create_endpoint():
    dto = UserCreate(username="alice", email="alice@example.com")
    assert dto.username == "alice"
```

## Dependency Direction

Dependencies flow inward:

```
Presentation → Domain ← Infrastructure
```

**Rules:**
- Presentation depends on Domain
- Infrastructure depends on Domain
- Domain depends on nothing (except standard library)

```python
# ✅ Good: Presentation depends on Domain
class UserView(ViewDTO[User]):  # Depends on User (Domain)
    id: int

# ✅ Good: Infrastructure depends on Domain
class UserRepository:
    def save(self, user: User) -> None:  # Depends on User (Domain)
        pass

# ❌ Bad: Domain depends on Infrastructure
class User(Domain):
    def save(self, db: Database) -> None:  # Domain shouldn't know about DB
        pass
```

## Cross-Layer Communication

### Presentation → Domain

Use BuildDTOs to convert external data to domain:

```python
# Presentation receives external data
dto = UserCreate(username="alice", email="alice@example.com")

# Convert to domain
user = dto.to_domain(id=generate_id())

# Domain is ready for business logic
user.activate()
```

### Domain → Presentation

Use ViewDTOs to convert domain to external representation:

```python
# Domain has business data
user = User(id=1, username="alice", email="alice@example.com")

# Convert to view
view = UserView.build(user)

# View is ready for external consumption
return view.model_dump()
```

### Domain ↔ Infrastructure

Domain and infrastructure communicate through interfaces:

```python
# Domain defines interface (conceptually)
class UserRepository:
    def save(self, user: User) -> None: ...

# Infrastructure implements interface
class DatabaseUserRepository(UserRepository):
    def save(self, user: User) -> None:
        db.session.add(user)
        db.session.commit()
```

## Separation in Practice

### Complete Example

```python
# Domain layer
class User(Domain):
    id: System[int]
    username: str
    email: str
    
    def activate(self) -> None:
        self.is_active = True

# Presentation layer
class UserCreate(BuildDTO[User]):
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str

@router.post("/users", response_model=UserView)
def create_user(dto: UserCreate) -> UserView:
    user = dto.to_domain(id=generate_id())
    user.activate()  # Business logic
    repository.save(user)  # Infrastructure
    return UserView.build(user)

# Infrastructure layer
class UserRepository:
    def save(self, user: User) -> None:
        db.session.add(user)
        db.session.commit()
```

## Benefits Summary

Separation of concerns provides:

- ✅ **Maintainability**: Changes isolated to one layer
- ✅ **Testability**: Each layer tested independently
- ✅ **Portability**: Domain logic works with any framework
- ✅ **Clarity**: Clear responsibilities for each component
- ✅ **Evolution**: Layers can evolve independently

## Next Steps

- Learn about [Domain-Driven Design](domain-driven-design.md) - how DDD supports separation
- Explore [Unidirectional Data Flow](unidirectional-data-flow.md) - how data flows between layers
- Understand [Data Transfer Objects](data-transfer-objects.md) - how DTOs enable separation

