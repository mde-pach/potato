# Installation

## Install Potato

=== "pip"

    ```bash
    pip install potato
    ```

=== "uv"

    ```bash
    uv add potato
    ```

## pyproject.toml

A typical project configuration:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "potato",
    "pydantic>=2.12.4",
]
```

## Mypy Plugin (Optional)

Potato validates all DTO definitions at class-definition time automatically. For additional Pydantic model support in mypy, enable the plugin:

```toml
[tool.mypy]
files = ["./src", "./tests"]
plugins = ["potato.mypy"]
mypy_path = "$MYPY_CONFIG_FILE_DIR"
```

This is optional — all Potato-specific validation happens at runtime regardless.

## IDE Setup

### VS Code

1. Install the Pylance extension
2. Set `python.analysis.typeCheckingMode` to `basic` or `strict`

### PyCharm

1. Enable type checking in Settings > Languages & Frameworks > Python > Type Checking
