# 🥔 Potato

**Type-safe Domain and DTO framework with compile-time validation**

Potato is an opinionated framework for building clean, type-safe data workflows between Domain models and Data Transfer Objects (DTOs). It extends Pydantic with a custom mypy plugin that catches configuration errors at compile-time, not runtime.

## 🎯 Key Features

- **Unidirectional Data Flow**: Clear separation between inbound (BuildDTO) and outbound (ViewDTO) data transformations
- **Compile-Time Validation**: Mypy plugin catches missing or incorrect field mappings before you run your code
- **Aggregate Support**: Declare complex domain relationships with automatic validation
- **Field Mapping**: Map DTO fields to Domain fields with different names using `Annotated` types
- **Zero Runtime Overhead**: All validation happens at compile-time via mypy

## 📦 Installation

```bash
# Install the package
pip install -e .

# Configure mypy (add to pyproject.toml)
[tool.mypy]
plugins = ["mypy_potato"]
```

## 🚀 Quick Start

### 1. Basic Domain Model

```python
from domain import Domain

class User(Domain):
    id: int
    username: str
    email: str
```

### 2. ViewDTO - Domain to External (Outbound)

```python
from typing import Annotated
from dto import ViewDTO

class UserView(ViewDTO[User]):
    id: int
    login: Annotated[str, User.username]  # Maps 'username' → 'login'
    email: str

# Usage
user = User(id=1, username="alice", email="alice@example.com")
view = UserView.build(user)
print(view.login)  # "alice"
```

**Compile-time safety**: If you forget a required field, mypy will catch it:

```python
# This would fail mypy validation
class IncorrectView(ViewDTO[User]):
    id: int
    email: str
    # ERROR: Missing required field 'username'
```

### 3. Aggregate Domains

For complex domains composed of multiple other domains:

```python
from domain.aggregates import Aggregate

class Price(Domain):
    amount: int
    currency: str

class Product(Domain):
    name: str

type Customer = User  # Type alias for clarity
type Seller = User

class Order(Domain[Aggregate[Customer, Seller, Price, Product]]):
    customer: Annotated[User, Customer]
    seller: Annotated[User, Seller]
    price_amount: Annotated[int, Price.amount]  # Extract just the amount
    product: Product

# Usage
order = Order(
    customer=alice,
    seller=bob,
    price_amount=100,
    product=widget
)
```

**Compile-time safety**: Mypy validates that all referenced Domain types are declared:

```python
# This would fail mypy validation
class OtherDomain(Domain):
    value: str

class BadOrder(Domain[Aggregate[User]]):
    user: User
    other: Annotated[str, OtherDomain.value]
    # ERROR: OtherDomain not declared in Aggregate
```

## 🧩 Core Concepts

### Domain Models

Domain models represent your core business logic and are independent of external representations:

```python
class User(Domain):
    id: int
    username: str
    email: str
    is_active: bool = True  # Optional field with default
```

- Extend `Domain` (which extends Pydantic's `BaseModel`)
- Contain business logic and validation
- Can reference fields from other domains using `Domain.field` syntax

### ViewDTO - Outbound Data Flow

ViewDTO creates immutable DTOs from Domain models for external consumption (API responses, etc.):

```python
class UserResponse(ViewDTO[User]):
    id: int
    username: str
    # Can rename fields
    active: Annotated[bool, User.is_active]

# Frozen (immutable) by default
view = UserResponse.build(user)
```

**Mypy validation ensures**:
- All required Domain fields are present in the DTO
- Field mappings reference valid Domain fields

### BuildDTO - Inbound Data Flow

BuildDTO creates DTOs for building Domain models from external data:

```python
class CreateUserRequest(BuildDTO[User]):
    username: str
    email: str

# In your API endpoint
dto = CreateUserRequest.build(user)
```

### Aggregates

Aggregates declare when a Domain is composed of multiple other Domains:

```python
class Order(Domain[Aggregate[User, Product, Price]]):
    user: User
    product: Product
    total: Annotated[int, Price.amount]
```

**Benefits**:
1. **Documentation**: Makes domain dependencies explicit
2. **Validation**: Mypy ensures all referenced domains are declared
3. **Type Safety**: Catch errors at compile-time

## 🔍 How It Works

### Field References via FieldProxy

When you access a field on a Domain class (not instance), you get a `FieldProxy`:

```python
User.username  # Returns FieldProxy(User, "username")
```

This enables field mapping in `Annotated` types:

```python
class UserDTO(ViewDTO[User]):
    login: Annotated[str, User.username]  # Maps username → login
```

### Mypy Plugin Validation

The `mypy_potato` plugin hooks into mypy's type checking to validate:

1. **ViewDTO Field Mappings**: 
   - Checks all required Domain fields are present in the DTO
   - Validates field mappings reference valid Domain fields

2. **Aggregate Declarations**:
   - Validates that Domain types referenced in fields are declared in `Aggregate[...]`
   - Ensures aggregate boundaries are explicit

## 📚 Examples

See [`src/main.py`](src/main.py) for comprehensive examples including:

- Basic Domain models
- ViewDTO with field mapping
- BuildDTO usage
- Aggregate domains
- Compile-time validation examples

Run the examples:

```bash
python src/main.py
```

Run mypy validation:

```bash
mypy src/main.py
```

## 🏗️ Architecture Philosophy

Potato enforces a unidirectional data flow:

```
External Data → BuildDTO → Domain → ViewDTO → External Data
```

### Benefits

1. **Type Safety**: Catch configuration errors at compile-time
2. **Clear Boundaries**: Explicit separation between domain and external representations
3. **Maintainability**: Changes to Domain models are validated against all DTOs
4. **Self-Documenting**: Aggregate declarations make dependencies explicit
5. **Refactoring Safety**: Rename a field? Mypy tells you everywhere it needs to update

## 🛠️ Development

### Project Structure

```
.
├── mypy_potato/          # Mypy plugin for compile-time validation
│   └── __init__.py
├── src/
│   ├── domain/           # Domain model implementation
│   │   ├── domain.py     # Domain base class and FieldProxy
│   │   └── aggregates.py # Aggregate marker type
│   ├── dto.py            # ViewDTO and BuildDTO base classes
│   └── main.py           # Usage examples
├── pyproject.toml        # Project configuration
└── README.md
```

### Running Tests

```bash
# Type checking
mypy src/

# Run examples
python src/main.py
```

## 🤔 When to Use Potato

**Good fit**:
- APIs with clear domain models and DTOs
- Applications requiring strong type safety
- Projects where compile-time validation prevents runtime errors
- Teams that value explicit, self-documenting code

**Not a good fit**:
- Simple CRUD apps where DTOs mirror domains exactly
- Prototypes where flexibility > safety
- Projects not using mypy

## 📖 Related Concepts

Potato is inspired by:
- **Domain-Driven Design (DDD)**: Clear domain boundaries and aggregates
- **Clean Architecture**: Separation of domain logic from external concerns
- **Type-Driven Development**: Using types to prevent entire classes of bugs

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional validation rules in the mypy plugin
- Performance optimizations
- More comprehensive examples
- Documentation improvements

## 📄 License

MIT License - see LICENSE file for details

---

**Made with 🥔 by developers who believe types should work for you**
