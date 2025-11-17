# Optional Fields Update

## Summary

The mypy plugin has been updated to support optional fields with default values. Fields that have explicit default values in the Domain model are no longer required in ViewDTOs.

## Changes Made

### Before
- **All** Domain fields were required to be present in ViewDTOs
- No distinction between required and optional fields

### After
- **Only required fields** (without defaults) must be present in ViewDTOs
- **Optional fields** (with defaults) can be omitted from ViewDTOs
- This aligns with DTO semantics where default values don't need to be provided

## Implementation

The plugin now:
1. Separates Domain fields into two sets: `required_fields` and `optional_fields`
2. Uses `var.has_explicit_value` to detect fields with explicit default values
3. Only validates that required fields are present in the ViewDTO
4. Optional fields can be included or omitted as needed

## Example

```python
from domain import Domain
from dto import ViewDTO
from typing import Annotated, Optional

class User(Domain):
    id: int                      # Required
    username: str                # Required
    bio: str = ""                # Optional (has default)
    is_active: bool = True       # Optional (has default)
    tutor: Optional[str] = None  # Optional (has default)

# ✅ Valid: All required fields present, optional omitted
class UserView(ViewDTO[User]):
    id: int
    username: str
    # bio, is_active, and tutor can be omitted

# ✅ Valid: Including optional fields is fine
class UserViewDetailed(ViewDTO[User]):
    id: int
    username: str
    bio: str
    is_active: bool

# ❌ Invalid: Missing required field 'username'
class UserViewBad(ViewDTO[User]):
    id: int
    # Error: missing required field "username"
```

## Benefits

1. **More Flexible DTOs**: ViewDTOs don't need to include fields with sensible defaults
2. **Better Semantics**: Aligns with the concept that DTOs represent data transfer, not storage
3. **Cleaner Code**: Reduces boilerplate when many fields have default values
4. **Type Safety**: Still validates all required fields are present

## Testing

All validation scenarios work correctly:
- ✅ Required fields with direct name matching
- ✅ Required fields with `Annotated` mapping
- ✅ Optional fields can be omitted
- ✅ Optional fields can be included if needed
- ❌ Missing required fields trigger errors
- ❌ Invalid field mappings trigger errors

Run tests with:
```bash
uv run mypy src/
```

