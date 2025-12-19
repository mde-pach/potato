# Type Safety

Potato provides **compile-time type safety** to catch errors before they reach production. This is a core philosophy: catch mistakes early, when they're cheapest to fix.

## Why Type Safety?

Type safety helps you:

- **Catch errors early**: Find bugs before runtime
- **Improve refactoring**: Confidently change code knowing types will catch mistakes
- **Document code**: Types serve as inline documentation
- **Enable tooling**: IDEs can provide better autocomplete and error detection

## Three Layers of Type Safety

Potato provides type safety at three levels:

### 1. Static Typing

All DTOs and Domains use Python type hints:

```python
class User(Domain):
    id: int  # Not str, not None - exactly int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int  # Must match User.id type
    username: str  # Must match User.username type
    email: str  # Must match User.email type
```

**Benefits:**
- Clear contracts between components
- IDE autocomplete and error detection
- Self-documenting code

### 2. Runtime Validation

Pydantic validation ensures data integrity at runtime:

```python
from pydantic import ValidationError

try:
    dto = UserCreate(username="alice", email="invalid")  # Missing @
except ValidationError as e:
    print(e)  # Validation errors caught at runtime
```

**Benefits:**
- Catch invalid data from external sources
- Ensure data integrity before domain creation
- Provide clear error messages

### 3. Compile-Time Validation

The Mypy plugin catches errors **before runtime**:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    # Missing 'email' field - Mypy error at compile time!
```

**Benefits:**
- Catch errors before code runs
- Ensure ViewDTOs include all required fields
- Verify BuildDTOs exclude system fields
- Validate aggregate relationships

## Type Safety in Practice

### ViewDTO Validation

Mypy ensures ViewDTOs include all required fields:

```python
class User(Domain):
    id: int
    username: str
    email: str

class UserView(ViewDTO[User]):
    id: int
    username: str
    # Missing 'email' - Mypy error!
```

### BuildDTO Validation

Mypy ensures BuildDTOs exclude system fields:

```python
class User(Domain):
    id: System[int]
    username: str
    email: str

class UserCreate(BuildDTO[User]):
    id: int  # Error! System fields can't be in BuildDTO
    username: str
    email: str
```

### Field Type Matching

Mypy ensures field types match:

```python
class User(Domain):
    id: int
    username: str

class UserView(ViewDTO[User]):
    id: str  # Error! Must be int to match User.id
    username: str
```

### Aggregate Validation

Mypy validates aggregate relationships:

```python
class Order(Aggregate[User, Product]):
    customer: User
    product: Product
    # Missing required domains - Mypy error!
```

## Type Safety Philosophy

### Fail Fast

Type errors should be caught as early as possible:

1. **Compile time** (Mypy): Catch structural errors
2. **Runtime** (Pydantic): Catch data validation errors
3. **Never**: Let invalid data reach business logic

### Explicit Over Implicit

Types should be explicit, not inferred:

```python
# ✅ Good: Explicit types
class UserView(ViewDTO[User]):
    id: int
    username: str

# ❌ Bad: Relying on inference
class UserView(ViewDTO[User]):
    id = Field(...)  # Type not explicit
    username = Field(...)
```

### Type as Documentation

Types serve as documentation:

```python
class UserView(ViewDTO[User]):
    id: int  # Clearly an integer
    username: str  # Clearly a string
    email: str  # Clearly a string
```

## Enabling Type Safety

### Mypy Configuration

Enable the Potato Mypy plugin in `mypy.ini`:

```ini
[mypy]
plugins = potato.mypy

[mypy-*.migrations.*]
ignore_errors = True
```

### Type Checking in CI

Run type checking as part of your CI pipeline:

```bash
mypy src/ tests/
```

### IDE Integration

Most modern IDEs support Mypy:

- **VS Code**: Python extension with Pylance
- **PyCharm**: Built-in type checking
- **Vim/Neovim**: ALE or coc.nvim

## Next Steps

- Learn about [Mypy Plugin](../mypy.md) - detailed guide to compile-time validation
- Explore [ViewDTO](../core/viewdto.md) - see type safety in action
- Understand [BuildDTO](../core/builddto.md) - see type safety in action

