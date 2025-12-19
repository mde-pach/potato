# Mypy Plugin

Potato includes a **Mypy plugin** that provides compile-time validation for your DTOs and Domains.

## Why Use the Mypy Plugin?

The plugin catches errors **before runtime**:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)
    # Missing 'email' field - Mypy will catch this!
```

**Without the plugin**: Error at runtime when you try to build the DTO\
**With the plugin**: Error at type-check time, before running your code

## Installation

### Step 1: Install Potato

```bash
pip install potato
```

### Step 2: Enable the Plugin

Create or update your `mypy.ini`:

```ini
[mypy]
plugins = potato.mypy
check_untyped_defs = True
```

Or in `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["potato.mypy"]
check_untyped_defs = true
```

### Step 3: Run Mypy

```bash
mypy src/
```

## Features

The Mypy plugin validates:

### 1. Field Mapping Validation

**What it catches**: Field mappings must point to existing domain fields

```python
class User(Domain):
    username: str

# ❌ Error: 'unknown_field' doesn't exist
class BadUserView(ViewDTO[User]):
    login: str = Field(source=User.unknown_field)

# ✅ Correct
class GoodUserView(ViewDTO[User]):
    login: str = Field(source=User.username)
```

**Error message:**

```
ViewDTO "BadUserView" field "login" maps to non-existent Domain field "unknown_field" in "User"
```

### 2. Aggregate Validation

**What it catches**: All domain types used in an Aggregate must be declared in its generic parameters

```python
class User(Domain):
    name: str

class Order(Domain):
    amount: int

# ❌ Error: Order not declared in Aggregate generic
class BadAggregate(Aggregate[User]):
    user: User
    order: Order  # Error!

# ✅ Correct
class GoodAggregate(Aggregate[User, Order]):
    user: User
    order: Order
```

**Error message:**

```
Field "order" has type "Order" which is not declared in the Aggregate generic
```

### 3. Domain Aliasing

**What it validates**: Domain aliases (via `.alias()`) are correctly typed

```python
class User(Domain):
    name: str

# Create an alias
Buyer = User.alias("buyer")

# ✅ Mypy knows Buyer is a valid type
class OrderAggregate(Aggregate[User, Buyer]):
    seller: User
    buyer: Buyer
```

## Field Mapping Styles

The plugin supports both field mapping styles:

### Style 1: `Field(source=...)`

```python
class UserView(ViewDTO[User]):
    login: str = Field(source=User.username)
```

### Style 2: `Annotated`

```python
from typing import Annotated

class UserView(ViewDTO[User]):
    login: Annotated[str, User.username]
```

Both are validated by the plugin.

## Typed Context

The plugin validates `ViewDTO[Domain, Context]` syntax:

```python
class UserContext:
    is_admin: bool

# ✅ Correct: ViewDTO with context type
class UserView(ViewDTO[User, UserContext]):
    username: str
    
    @computed
    def display_name(self, context: UserContext) -> str:
        return f"Admin: {self.username}" if context.is_admin else self.username
```

## Configuration

### Basic Configuration

```ini
[mypy]
plugins = potato.mypy
```

### Recommended Settings

For best results, enable these Mypy settings:

```ini
[mypy]
plugins = potato.mypy

# Type checking
check_untyped_defs = True
disallow_untyped_defs = True
disallow_any_generics = True

# Strictness
warn_redundant_casts = True
warn_unused_ignores = True
warn_return_any = True

# Error reporting
show_error_codes = True
show_column_numbers = True
```

### Per-Module Configuration

Exclude specific modules from strict checks:

```ini
[mypy]
plugins = potato.mypy

[mypy-tests.*]
disallow_untyped_defs = False
```

## IDE Integration

The Mypy plugin works with IDE integrations:

### VS Code

Install the **Mypy** extension and configure:

```json
{
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": [
    "--config-file=mypy.ini"
  ]
}
```

### PyCharm

1. Go to **Settings → Tools → Mypy**
1. Enable **Mypy**
1. Set **Configuration file** to `mypy.ini`

## Troubleshooting

### Plugin Not Found

**Error**:

```
Error: Cannot find module 'potato.mypy'
```

**Solution**: Make sure Potato is installed in the same environment as Mypy:

```bash
pip install potato
# or
uv add potato
```

### False Positives

If the plugin reports incorrect errors, you can:

1. **Use `# type: ignore[misc]`** to suppress specific errors:

```python
class UserView(ViewDTO[User]):
    id: int
    login: str = Field(source=User.username)  # type: ignore[misc]
```

**Report an issue** on GitHub if you believe it's a bug

### Performance

The plugin adds minimal overhead to Mypy. For large codebases:

```ini
[mypy]
plugins = potato.mypy
incremental = True  # Cache results
```

## How It Works

The plugin hooks into Mypy's type checking process:

1. **Class Definition Hook**: Intercepts `ViewDTO`, `BuildDTO`, `Aggregate` class definitions
1. **Type Analysis**: Extracts generic type parameters (e.g., `ViewDTO[User]`)
1. **Validation**: Checks field presence, mappings, and aggregate declarations
1. **Error Reporting**: Emits Mypy errors with helpful messages

## Limitations

The plugin has some limitations:

- **Dynamic field creation**: Can't validate fields created at runtime
- **Complex generics**: Some edge cases with deeply nested generics may not be validated
- **Third-party types**: May not work with custom type systems

## Summary

The Mypy plugin provides:

| Feature        | What It Validates                   |
| -------------- | ----------------------------------- |
| Field Mappings | Mappings point to existing fields   |
| Aggregates     | All domains are declared in generic |
| Aliasing       | Domain aliases are properly typed   |

______________________________________________________________________

**Next Steps:**

- [Configure Mypy](https://mypy.readthedocs.io/en/stable/config_file.html) for your project
- [Best Practices](guides/patterns.md) for using Potato with Mypy
