# Potato Specifications

This document defines the specifications for the "Potato" library, a Python framework for type-safe DTOs and unidirectional data flow. It outlines the core concepts, the "ideal" API (including proposed improvements), and best practices.

## 1. Core Concepts

### 1.1 The Golden Rule: Isolation
**Domains must never be exposed.**
- They must not appear in API signatures (inbound or outbound).
- They must not be returned by controllers.
- They are for **internal business logic only**.

### 1.2 Unidirectional Data Flow
Potato enforces a strict separation between internal domain models and external data representations.
- **Inbound (`BuildDTO`)**: Data coming *into* your application (e.g., API requests) is validated and transformed into Domain models.
- **Domain**: Rich business objects that encapsulate logic and state.
- **Outbound (`ViewDTO`)**: Domain models are transformed into immutable DTOs for external consumption (e.g., API responses).

### 1.3 The Domain & System Fields
The `Domain` is the source of truth. It represents valid, persisted state.

**System Fields (`System[T]`)**:
Some fields (like IDs or audit timestamps) are managed by the system (Database, Service). They are required for the Domain to exist but are often missing during creation.
Potato handles this with the `System[T]` type alias.

```python
from potato import Domain, System

class User(Domain):
    # System[int] behaves exactly like 'int' at runtime
    # But it tells Potato: "This field is managed by the system"
    id: System[int]
    created_at: System[datetime]
    
    username: str
    email: str
    is_active: bool = True
```

**Behavior:**
- **In Domain**: `id` is required (it's just an `int`).
- **In BuildDTO**: `id` is automatically excluded (because it's `System[...]`).

### 1.4 Aggregates as Contexts
An `Aggregate` is not just a group of objects; it is an **Encapsulated Context**. It defines a consistency boundary where multiple domains interact.

```python
# OrderContext defines a boundary where User and Order interact
class OrderContext(Aggregate[User, Order]):
    """
    This aggregate encapsulates the relationship between a User and their Order.
    It ensures that when we view an Order, we do so in the context of its User.
    """
    pass
```

## 2. API Specification

### 2.1 Defining a ViewDTO (Outbound)

#### Basic Projection
Map fields directly from the Domain by name.

```python
from potato import ViewDTO

class UserPublic(ViewDTO[User]):
    username: str  # Automatically maps from User.username
    # email is omitted, so it won't be exposed
```

#### Field Mapping (Syntax Sugar)
Use `Field(source=...)` to map fields that have different names or come from specific domains in an aggregate.

```python
from potato import ViewDTO, Field

class UserProfile(ViewDTO[User]):
    display_name: str = Field(source=User.username)
    contact_email: str = Field(source=User.email)
```

### 2.2 Advanced Features

#### Typed Context & Computed Fields
Pass runtime context to the build process in a type-safe way.
Use the `@computed` decorator for logic-based fields. Potato uses **Smart Injection** to pass the context only if requested.

```python
from pydantic import BaseModel
from potato import ViewDTO, computed

# Define your context structure
class UserContext(BaseModel):
    is_admin: bool
    viewer_id: int

# ViewDTO accepts the Domain AND the ContextType
class UserView(ViewDTO[User, UserContext]):
    is_admin: bool
    full_name: str
    
    # Context is requested in signature, so it is injected
    @computed
    def is_admin(self, user: User, context: UserContext) -> bool:
        return context.is_admin
        
    # Context NOT requested, so not injected
    @computed
    def full_name(self, user: User) -> str:
        return f"{user.first} {user.last}"
```

#### Nested DTOs
Embed other DTOs to create rich, hierarchical responses.

```python
class PostView(ViewDTO[Post]):
    title: str
    comments: list[CommentView] 
```

### 2.3 Building DTOs
DTOs are instantiated using the `build()` factory method.

```python
# Single Domain
user = User(id=1, username="alice", ...)
view = UserProfile.build(user)

# With Context
context = UserContext(is_admin=True, viewer_id=99)
view = UserView.build(user, context=context)
```

## 3. Typing & Static Analysis
Potato is designed for **Compiler-Driven Development**.
- **Mypy Plugin**: A dedicated plugin ensures that all mappings are valid at compile time.
- **No Runtime Surprises**: If it compiles, the mapping is valid.

## 4. Future Improvements

- **Implicit Type Inference**: Allow `login = Field(source=User.username)` without explicit type annotation.
- **Validation Groups**: Reuse BuildDTOs for different scenarios (Create vs Update).
