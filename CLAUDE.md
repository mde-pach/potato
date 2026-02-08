# Potato - Claude Code Guide

**Type-safe DTOs for clean architecture in Python**

## Project Overview

Potato is a Python library that enforces clean separation between domain models and external data representations. Built on Pydantic v2, it provides type-safe Data Transfer Objects (DTOs) with class-definition-time validation via metaclasses.

### Key Capabilities
- Unidirectional data flow with ViewDTO (outbound) and BuildDTO (inbound)
- Field mapping with `Field(source=...)`
- Computed fields with `@computed` decorator
- Auto-managed fields with `Auto[T]`
- Private fields with `Private[T]` (never exposed in DTOs)
- Type-safe field-based aggregates for multi-domain composition
- Nested ViewDTO auto-building
- ViewDTO inheritance
- Partial BuildDTOs with `apply_to()`
- Field transforms and visibility
- Lifecycle hooks (`@before_build`, `@after_build`)
- Deep field flattening
- Class-definition-time validation via metaclasses

## Architecture

### Core Components

1. **Domain Models** (`src/potato/domain/`)
   - `Domain`: Base class for domain models
   - `Aggregate`: Compose multiple domains (field-based, no generics)
   - Auto-managed fields marked with `Auto[T]`
   - Private fields marked with `Private[T]`

2. **DTOs** (`src/potato/dto/`)
   - `ViewDTO[T]`: Outbound transformations (domain -> external)
   - `BuildDTO[T]`: Inbound transformations (external -> domain)
   - `BaseDTO`: Shared base functionality (DTOMeta)

3. **Mypy Plugin** (`src/potato/mypy.py`)
   - Thin stub that delegates to Pydantic's mypy plugin
   - All Potato-specific validation is done at class-definition time in metaclasses

4. **Types & Introspection** (`src/potato/types.py`, `src/potato/introspection.py`)
   - `FieldProxy`: Field reference with namespace and path support
   - `DomainFieldAccessor`: Proxy for `Aggregate.field.subfield` access
   - Runtime introspection for field metadata

## Development Workflow

### Setup
```bash
uv sync  # Install dependencies
```

### Running Tests
```bash
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest tests/test_*.py    # Run specific test file
uv run pytest -k "test_name"     # Run specific test
uv run pytest --cov=src/potato   # With coverage
```

### Type Checking
```bash
uv run mypy src/              # Check source code
uv run mypy tests/            # Check tests
uv run mypy main.py           # Check example file
```

### Documentation
```bash
uv run mkdocs serve  # Serve docs locally at http://127.0.0.1:8000
uv run mkdocs build  # Build static docs
```

### Linting
```bash
uv run ruff check src/ tests/  # Check code
uv run ruff format src/ tests/ # Format code
```

## Code Conventions

### Style
- Python 3.14+ (strict type hints required)
- Use Pydantic v2 features and patterns
- Immutability by default (ViewDTOs are frozen)
- Explicit is better than implicit

### Naming
- `ViewDTO` for outbound transformations
- `BuildDTO` for inbound transformations
- Use `Auto[T]` for auto-generated/managed fields
- Use `Private[T]` for never-exposed fields
- Computed fields use `@computed` decorator
- Field mapping uses `Field(source=...)` exclusively

### Testing
- Tests live in `tests/` directory
- Use pytest fixtures in `tests/conftest.py`
- Validation tests are in `tests/plugin/test_mypy_plugin.py` (runtime tests, no mypy dependency)

## Public API

```python
from potato import (
    Domain,        # Base for domain models
    Aggregate,     # Multi-domain container (field-based)
    ViewDTO,       # Domain -> External (frozen)
    BuildDTO,      # External -> Domain
    Field,         # Field configuration (source, transform, visible)
    Auto,          # Auto-generated fields (id, timestamps)
    Private,       # Never-exposed fields (password_hash)
    computed,      # Decorator for computed fields
    before_build,  # Lifecycle hook: before ViewDTO construction
    after_build,   # Lifecycle hook: after ViewDTO construction
)
```

## Key Patterns

### ViewDTO
```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)

view = UserView.from_domain(user)
views = UserView.from_domains(users)
```

### BuildDTO
```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str

user = dto.to_domain(id=1)

# Partial updates
class UserUpdate(BuildDTO[User], partial=True):
    username: str

updated = update.apply_to(existing_user)
```

### Aggregates
```python
class Order(Aggregate):
    customer: User
    product: Product
    quantity: int

class OrderView(ViewDTO[Order]):
    customer_name: str = Field(source=Order.customer.username)
    product_name: str = Field(source=Order.product.name)
    quantity: int
```

## Important Files

- `src/potato/__init__.py` - Public API exports
- `src/potato/core.py` - Core utilities (Auto, Private, Field, computed, hooks)
- `src/potato/types.py` - FieldProxy, DomainFieldAccessor
- `src/potato/introspection.py` - Field mapping extraction
- `src/potato/mypy.py` - Thin mypy stub (delegates to Pydantic)
- `src/potato/domain/domain.py` - Domain base class with DomainMeta
- `src/potato/domain/aggregates.py` - Aggregate with AggregateMeta
- `src/potato/dto/base.py` - DTOMeta (partial support)
- `src/potato/dto/view.py` - ViewDTOMeta + ViewDTO
- `src/potato/dto/build.py` - BuildDTO
- `pyproject.toml` - Project configuration and dependencies
- `mkdocs.yml` - Documentation configuration
- `main.py` - Example/testing file

## Testing Strategy

### Unit Tests
- Test individual DTO transformations
- Test field mapping and computed fields
- Test Auto/Private field handling
- Test aggregate composition

### Validation Tests
- Runtime metaclass validation tests
- Test that invalid DTOs are caught at class-definition time
- Test proper error messages with hints

### Feature Tests
- Test nested ViewDTO auto-building
- Test ViewDTO inheritance
- Test Field(transform=...) and Field(visible=...)
- Test partial BuildDTOs and apply_to()
- Test lifecycle hooks (@before_build, @after_build)
- Test deep field flattening

## Key Concepts

1. **Unidirectional Data Flow**
   - `ViewDTO`: domain -> external (read-only, immutable)
   - `BuildDTO`: external -> domain (provides construction data)

2. **Auto Fields**
   - Marked with `Auto[T]` in domain models
   - Auto-excluded from BuildDTOs
   - Included normally in ViewDTOs

3. **Private Fields**
   - Marked with `Private[T]` in domain models
   - Auto-excluded from BuildDTOs
   - Forbidden in ViewDTOs (TypeError at class-definition time)

4. **Field Mapping**
   - Use `Field(source=DomainModel.field_name)` for renaming
   - Supports deep access: `Field(source=User.address.city)`
   - Supports transforms: `Field(transform=lambda x: x.upper())`
   - Supports visibility: `Field(visible=lambda ctx: ctx.is_admin)`

5. **Aggregates**
   - Field-based composition (no generic parameters)
   - Field names serve as namespaces
   - `Aggregate.field.subfield` for ViewDTO mapping

6. **Computed Fields**
   - Use `@computed` decorator
   - Receive domain instance as parameter
   - Add derived/calculated data to views

## Debugging Tips

- Validation errors are raised as TypeError/AttributeError at class-definition time
- Error messages include hints on how to fix the issue
- Run tests with `-v` for verbose output
- Use `pytest --pdb` to drop into debugger on failures

## Resources

- **Documentation**: See `docs/` directory
- **Examples**: See `example/` directory and `main.py`
- **Tests**: See `tests/` directory for usage patterns
- **README**: See `README.md` for quick overview
