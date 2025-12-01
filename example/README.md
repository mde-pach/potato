# Potato Example - Blog Management System

A comprehensive example application demonstrating the **potato** package using FastAPI with Domain-Driven Design (DDD) architecture, dependency injection, repository pattern, and SQLAlchemy ORM.

## 🎯 What This Example Demonstrates

### Potato Package Features

1. **ViewDTO** (Outbound Data)
   - Field mapping: `login` from `username` using `Field(source=...)`
   - Computed fields: `@computed` decorator for derived data
   - Building from aggregates with multiple domains
   - Immutability by default

2. **BuildDTO** (Inbound Data)
   - Automatic `System[T]` field exclusion
   - `to_domain()` conversion
   - Pydantic validation

3. **Aggregates**
   - `PostAggregate`: Post + User (author)
   - `CommentAggregate`: Comment + User (author) + Post
   - Type-safe multi-domain composition

4. **System Fields**
   - `System[int]` for auto-generated IDs
   - `System[datetime]` for timestamps
   - Excluded from BuildDTO, required in ViewDTO

### Architecture Features

- **DDD Layered Architecture**: Domain → Infrastructure → Application → Presentation
- **Repository Pattern**: Abstract interfaces with SQLAlchemy implementations
- **Dependency Injection**: Clean service dependencies via FastAPI
- **SQLAlchemy 2.0**: Modern ORM with type hints
- **SQLite Database**: Simple, file-based database

## 📁 Project Structure

```
example/
├── domain/                     # Domain Layer (Business Logic)
│   ├── models.py              # Domain models: User, Post, Comment
│   ├── aggregates.py          # PostAggregate, CommentAggregate
│   └── repositories/          # Repository interfaces
│
├── infrastructure/            # Infrastructure Layer (Technical)
│   ├── database/
│   │   ├── models.py         # SQLAlchemy models
│   │   └── repositories/     # Repository implementations
│   └── mappers.py            # Domain ↔ DB mapping
│
├── application/              # Application Layer (Use Cases)
│   ├── dtos/                 # ViewDTOs and BuildDTOs
│   │   ├── user_dtos.py
│   │   ├── post_dtos.py
│   │   └── comment_dtos.py
│   └── services/             # Business services
│
├── presentation/             # Presentation Layer (API)
│   ├── routers/              # FastAPI routers
│   └── dependencies.py       # DI configuration
│
├── main.py                   # FastAPI application
├── database.py               # Database setup
└── config.py                 # Configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Navigate to example directory
cd example

# Install dependencies with uv
uv pip install -e ..

# Or with pip
pip install -e ..
pip install fastapi uvicorn sqlalchemy pydantic-settings
```

### Run the Application

```bash
# From the example directory
cd example

# Run with uvicorn
python -m uvicorn main:app --reload

# Or specify host and port
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Examples

### Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Wonder"
  }'
```

**Response** (ViewDTO with field mapping & computed fields):
```json
{
  "id": 1,
  "login": "alice",              // Mapped from username
  "email": "alice@example.com",
  "full_name": "Alice Wonder",
  "created_at": "2024-11-22T22:00:00",
  "is_active": true,
  "display_name": "@alice",       // Computed field
  "account_age_days": 0           // Computed field
}
```

### Create a Post

```bash
curl -X POST http://localhost:8000/api/v1/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is an example blog post demonstrating the potato package.",
    "author_id": 1
  }'
```

**Response** (ViewDTO from PostAggregate):
```json
{
  "id": 1,
  "title": "My First Post",
  "content": "This is an example blog post...",
  "created_at": "2024-11-22T22:01:00",
  "updated_at": "2024-11-22T22:01:00",
  "published": false,
  "author_id": 1,
  "author_name": "alice",          // From User domain
  "author_full_name": "Alice Wonder", // From User domain
  "excerpt": "This is an example blog post..."  // Computed field
}
```

### Create a Comment

```bash
curl -X POST http://localhost:8000/api/v1/posts/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great post!",
    "author_id": 1,
    "post_id": 1
  }'
```

**Response** (ViewDTO from CommentAggregate with 3 domains):
```json
{
  "id": 1,
  "content": "Great post!",
  "created_at": "2024-11-22T22:02:00",
  "author_id": 1,
  "author_name": "alice",         // From User domain
  "post_id": 1,
  "post_title": "My First Post",  // From Post domain
  "author_display": "@alice"      // Computed field
}
```

### List Posts (with filtering)

```bash
# All posts
curl http://localhost:8000/api/v1/posts

# Published posts only
curl http://localhost:8000/api/v1/posts?published_only=true

# With pagination
curl http://localhost:8000/api/v1/posts?skip=0&limit=10
```

## 🔍 Code Walkthrough

### 1. Domain Models with System Fields

```python
# domain/models.py
from potato import Domain, System

class User(Domain):
    id: System[int]              # Auto-generated, excluded from BuildDTO
    username: str
    email: str
    created_at: System[datetime] # System-managed timestamp
    is_active: bool = True
```

### 2. ViewDTO with Field Mapping

```python
# application/dtos/user_dtos.py
from potato import ViewDTO, Field, computed

class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # Field mapping!
    email: str
    created_at: datetime
    
    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"           # Computed field!
```

### 3. BuildDTO with System Field Exclusion

```python
# application/dtos/user_dtos.py
from potato import BuildDTO

class UserCreate(BuildDTO[User]):
    username: str
    email: str
    full_name: str
    # id and created_at are automatically excluded!
```

### 4. Aggregates for Multi-Domain Views

```python
# domain/aggregates.py
from potato import Aggregate

class PostAggregate(Aggregate[Post, User]):
    post: Post
    author: User

# application/dtos/post_dtos.py
from typing import Annotated

class PostView(ViewDTO[PostAggregate]):
    id: Annotated[int, PostAggregate.post.id]
    title: Annotated[str, PostAggregate.post.title]
    author_name: Annotated[str, PostAggregate.author.username]  # From User!
```

### 5. Repository Pattern

```python
# domain/repositories/user_repository.py (Interface)
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User: pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: pass

# infrastructure/database/repositories/user_repository.py (Implementation)
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user: User) -> User:
        db_user = domain_user_to_db(user)
        self.session.add(db_user)
        self.session.commit()
        return db_user_to_domain(db_user)
```

### 6. Service Layer

```python
# application/services/user_service.py
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def create_user(self, user_create: UserCreate) -> UserView:
        # Convert BuildDTO → Domain
        user = user_create.to_domain(id=0, created_at=datetime.utcnow())
        
        # Business logic & persistence
        created_user = self.user_repository.create(user)
        
        # Convert Domain → ViewDTO
        return UserView.build(created_user)
```

### 7. FastAPI Router

```python
# presentation/routers/users.py
@router.post("", response_model=UserView)
def create_user(
    user_create: UserCreate,                    # BuildDTO for input
    service: UserService = Depends(get_user_service),
) -> UserView:                                   # ViewDTO for output
    return service.create_user(user_create)
```

## 🎓 Key Takeaways

### Potato Package Benefits

1. **Type Safety**: Mypy plugin catches missing fields at compile time
2. **Clean Separation**: DTOs separate API from domain models
3. **Explicit Transformations**: Clear data flow in/out of domain
4. **System Fields**: Proper handling of auto-generated data
5. **Aggregates**: Type-safe multi-domain composition

### DDD Architecture Benefits

1. **Maintainability**: Clear layer separation
2. **Testability**: Mock repositories, test domain in isolation
3. **Flexibility**: Swap infrastructure without touching domain
4. **Clarity**: Each layer has a single responsibility

## 🔧 Development

### Run Tests (TODO)

```bash
pytest
```

### Type Checking

```bash
mypy .
```

### Database

The example uses SQLite with a file database (`example_blog.db`). To reset:

```bash
rm example_blog.db
# Restart the application to recreate
```

## 📖 Learn More

- [Potato Documentation](../docs/index.md)
- [ViewDTO Guide](../docs/core/viewdto.md)
- [BuildDTO Guide](../docs/core/builddto.md)
- [Aggregates Guide](../docs/core/aggregates.md)

## 📝 License

This example is part of the Potato package and follows the same MIT license.
