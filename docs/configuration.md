# Configuration

Configure Potato and related tools for your project.

## Mypy Plugin

Potato includes a mypy plugin for compile-time validation of DTOs and aggregates. Enable it in your `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["potato.mypy"]
```

That's it! The plugin will automatically validate:

- Aggregate declarations
- Field mappings in ViewDTOs
- Domain aliasing usage

## Project Configuration

### pyproject.toml

A typical `pyproject.toml` configuration:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "potato",
    "pydantic>=2.12.4",
]

[tool.mypy]
files = ["./src", "./tests"]
plugins = ["potato.mypy"]
mypy_path = "$MYPY_CONFIG_FILE_DIR"
```

### IDE Setup

#### VS Code

1. Install the Pylance extension
1. Ensure `python.analysis.typeCheckingMode` is set to `basic` or `strict`
1. Mypy will use the plugin automatically

#### PyCharm

1. Enable mypy integration in Settings → Languages & Frameworks → Python → Type Checking
1. The plugin will be used automatically

## Type Checking

Run mypy to check your code:

```bash
mypy src/
```

Or with pytest-mypy:

```bash
pytest --mypy
```

## Common Configuration Issues

### Plugin Not Found

If you see `error: Cannot find plugin 'potato.mypy'`:

1. Ensure Potato is installed: `pip install potato`
1. Check that `plugins = ["potato.mypy"]` is in `[tool.mypy]` section
1. Verify mypy can find the plugin: `mypy --show-traceback`

### Type Errors with Aggregates

If you see type errors with aggregates:

1. Ensure all referenced domains are in the `Aggregate[...]` declaration
1. Check that field mappings use correct domain types
1. Verify aliases are created before use

## Next Steps

- **[Quickstart](quickstart.md)** - Get started with Potato
- **[Domain Models](core/domain.md)** - Learn about domain models
- **[API Reference](api-reference.md)** - Full API documentation
