# Configuration

## Mypy Plugin

Potato ships a thin mypy plugin that delegates to Pydantic's plugin. This is **optional** — all Potato-specific validation happens at class-definition time automatically.

```toml
[tool.mypy]
files = ["./src", "./tests"]
plugins = ["potato.mypy"]
mypy_path = "$MYPY_CONFIG_FILE_DIR"
```

## Runtime Validation

Potato validates DTO and Aggregate definitions automatically at class-definition time. No configuration needed — just define your classes and errors are caught at import time.

Validated rules:

| Rule | When | Error Type |
|------|------|------------|
| Field mappings point to existing domain fields | Class definition | `AttributeError` |
| Field mappings reference the correct domain | Class definition | `TypeError` |
| Private fields are not exposed in ViewDTOs | Class definition | `TypeError` |
| Aggregate domain types are inferred from fields | Class definition | `TypeError` |
| Deep field paths are valid | Class definition | `AttributeError` |

See [Error Messages](../advanced/error-messages.md) for examples of each error.

## Type Checking in CI

```bash
mypy src/ tests/
```
