# MyPy Plugin for ViewDTO Validation

## Overview

This mypy plugin validates that `ViewDTO` classes properly declare all **required** fields from their corresponding Domain models. It ensures type safety by catching missing or incorrectly mapped fields at static analysis time.

## Features

### 1. Required Field Validation
The plugin validates that every **required** field (without defaults) in the Domain model is present in the ViewDTO either:
- **By name**: A field with the same name exists in the ViewDTO
- **By mapping**: The field is mapped using `Annotated[type, Domain.field]`

### 2. Optional Field Handling
Fields with default values in the Domain model are **optional** in ViewDTOs:
- Fields with explicit defaults (e.g., `field: int = 0`) can be omitted
- This aligns with DTO semantics where defaults don't need to be provided

### 3. Mapping Validation
When using `Annotated` to map fields, the plugin verifies that:
- The referenced Domain field actually exists
- Invalid mappings trigger a clear error message

## Usage Examples

### ✅ Valid: Fields match by name
```python
class User(Domain):
    id: int
    username: str

class UserView(ViewDTO[User]):
    id: int
    username: str  # Matches Domain field name
```

### ✅ Valid: Using Annotated mapping
```python
class User(Domain):
    id: int
    username: str

class UserView(ViewDTO[User]):
    id: str
    login: Annotated[str, User.username]  # Maps 'login' to 'username'
```

### ✅ Valid: Optional fields with defaults can be omitted
```python
class User(Domain):
    id: int
    username: str
    bio: str = ""  # Optional field with default
    is_active: bool = True  # Optional field with default

class UserView(ViewDTO[User]):
    id: int
    username: str
    # bio and is_active can be omitted - they have defaults
```

### ❌ Invalid: Missing required field
```python
class User(Domain):
    id: int
    username: str

class UserView(ViewDTO[User]):
    id: str
    # Missing: username field or mapping
    # Error: ViewDTO "UserView" is missing required field "username" from Domain "User"
```

### ❌ Invalid: Incorrect mapping
```python
class User(Domain):
    id: int
    username: str

class UserView(ViewDTO[User]):
    id: str
    login: Annotated[str, User.nonexistent]
    # Error: ViewDTO "UserView" field "login" maps to non-existent Domain field "nonexistent"
```

## How It Works

1. **Hook Registration**: The plugin registers a `get_base_class_hook` for `dto.ViewDTO`
2. **Domain Type Extraction**: Extracts the Domain type from the generic parameter `ViewDTO[Domain]`
3. **Field Collection**: 
   - Collects required fields (without defaults) and optional fields (with defaults) from the Domain model
   - Collects all fields from the ViewDTO
   - Extracts field mappings from `Annotated` types
4. **Validation**:
   - Checks each **required** Domain field is present by name or mapped
   - Optional fields (with defaults) can be omitted from the ViewDTO
   - Validates mapped fields reference existing Domain fields
5. **Error Reporting**: Provides clear, actionable error messages

## Implementation Details

- **Unanalyzed Types**: Handles `UnboundType` for early-stage type analysis
- **Analyzed Types**: Handles `IndexExpr` for later-stage type analysis
- **AST Parsing**: Uses `stmt.unanalyzed_type` to access original type expressions
- **Field Mapping**: Parses `Annotated[type, Domain.field]` to extract the field name
- **Default Detection**: Uses `var.has_explicit_value` to identify fields with default values

## Configuration

The plugin is already configured in `pyproject.toml`:

```toml
[tool.mypy]
files = ["./src"]
plugins = ["mypy_potato"]
```

Run mypy to validate your code:
```bash
uv run mypy src/
```

