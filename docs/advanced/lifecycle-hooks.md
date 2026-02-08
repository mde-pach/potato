# Lifecycle Hooks

Lifecycle hooks let you inject logic before or after ViewDTO construction. Use them to enrich data, validate results, or trigger side effects.

## @before_build

Called before the ViewDTO is constructed. Returns a dict of extra data to merge into the ViewDTO fields:

```python
from potato import Domain, ViewDTO, Auto, before_build

class Order(Domain):
    id: Auto[int]
    reviewer_id: int
    total: int

class OrderView(ViewDTO[Order]):
    id: int
    total: int
    reviewer_name: str

    @before_build
    @classmethod
    def enrich(cls, entity, context=None):
        return {"reviewer_name": lookup_reviewer(entity.reviewer_id)}
```

### Auto-Wrapping

If you omit `@classmethod`, Potato wraps it automatically:

```python
class OrderView(ViewDTO[Order]):
    id: int
    reviewer_name: str

    @before_build
    def enrich(cls, entity, context=None):
        return {"reviewer_name": lookup_reviewer(entity.reviewer_id)}
    # Automatically wrapped as classmethod
```

### Signature

```python
@before_build
@classmethod
def hook_name(cls, entity: DomainType, context=None) -> dict[str, Any]:
    return {"extra_field": value}
```

The returned dict values are merged into the ViewDTO fields during construction.

## @after_build

Called after the ViewDTO is fully constructed (including computed fields). Use it for post-construction validation or logging:

```python
from potato import after_build

class AuditView(ViewDTO[Order]):
    id: int
    total: int

    @after_build
    def validate(self):
        if self.total < 0:
            raise ValueError("Total cannot be negative")
```

### Signature

```python
@after_build
def hook_name(self) -> None:
    ...
```

`@after_build` receives the fully constructed ViewDTO instance.

## Execution Order

The full construction sequence:

1. **@before_build** — compute extra data
2. **Field mapping** — extract values from domain
3. **@computed** — compute derived fields
4. **ViewDTO construction** — Pydantic model creation
5. **@after_build** — post-construction hooks

## Next Steps

- **[Computed Fields](../fundamentals/computed-fields.md)** — Derived fields
- **[ViewDTO](../fundamentals/viewdto.md)** — ViewDTO basics
- **[Visibility](visibility.md)** — Context-based field inclusion
